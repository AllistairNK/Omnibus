"""
RAG (Retrieval-Augmented Generation) service for enhanced chat completions.

This service integrates vector search with LLM generation to provide
context-aware responses with source attribution.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# LangChain 1.x imports
try:
    from langchain.chains import RetrievalQA, ConversationalRetrievalChain
    from langchain.chains.question_answering import load_qa_chain
    from langchain.chains.combine_documents.stuff import StuffDocumentsChain
    from langchain.chains.llm import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.schema import Document
    from langchain.memory import ConversationBufferMemory
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.chat_models import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Fallback for older versions or if LangChain is not fully installed
    LANGCHAIN_AVAILABLE = False
    # Define dummy classes to avoid import errors
    class ConversationalRetrievalChain:
        pass
    class PromptTemplate:
        def __init__(self, **kwargs):
            self.template = kwargs.get('template', '')
            self.input_variables = kwargs.get('input_variables', [])
        def format(self, **kwargs):
            return self.template
    class ConversationBufferMemory:
        pass
    class OpenAIEmbeddings:
        pass
    class Chroma:
        pass
    class ChatOpenAI:
        pass

from app.services.llm_service import LLMService
from app.services.similarity_search import SimilaritySearchService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for context-aware chat completions."""
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        similarity_search_service: Optional[SimilaritySearchService] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize RAG service.
        
        Args:
            llm_service: LLM service instance
            similarity_search_service: Similarity search service instance
            vector_store: Vector store instance
        """
        self.llm_service = llm_service or LLMService()
        self.similarity_search_service = similarity_search_service or SimilaritySearchService()
        self.vector_store = vector_store or VectorStore()
        
        # Initialize prompt templates
        self._initialize_prompts()
        
    def _initialize_prompts(self) -> None:
        """Initialize prompt templates for RAG."""
        # Enhanced RAG prompt with better context handling
        self.rag_prompt_template = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template="""You are an expert AI assistant with access to relevant documents. Your task is to provide accurate, helpful answers based on the provided context.

IMPORTANT INSTRUCTIONS:
1. Use the context below to answer the question.
2. If the context contains relevant information, base your answer primarily on it.
3. If the context doesn't contain enough information, acknowledge this and provide a general answer based on your knowledge.
4. When using information from the context, cite the source using [Document X, Chunk Y] format.
5. Be concise but thorough.
6. If the question is ambiguous or requires clarification, ask for more details.

CONTEXT FROM DOCUMENTS:
{context}

CHAT HISTORY (for context only):
{chat_history}

USER QUESTION: {question}

ASSISTANT RESPONSE:"""
        )
        
        # Multi-step reasoning prompt for complex questions
        self.reasoning_prompt_template = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template="""You are a reasoning assistant. Follow these steps:

1. Analyze the question and identify what information is needed.
2. Review the provided context and identify relevant information.
3. If context is insufficient, note what's missing.
4. Synthesize information from multiple sources if available.
5. Formulate a clear, accurate answer with citations.

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Think step by step, then provide your final answer:"""
        )
        
        # Prompt for source attribution and citation generation
        self.source_attribution_prompt = PromptTemplate(
            input_variables=["context", "question", "answer"],
            template="""Analyze the following answer and identify which specific sources from the context were used.

Context Documents:
{context}

Question: {question}

Generated Answer: {answer}

For each claim or piece of information in the answer, identify which document chunks support it. Return a JSON array where each object has:
- "claim": The specific claim from the answer
- "supporting_chunks": Array of chunk references that support this claim
- "confidence": High/Medium/Low based on how well the context supports the claim

Chunk references should be in format: "document_id:chunk_index"."""
        )
        
        # Prompt for handling conflicting information
        self.conflict_resolution_prompt = PromptTemplate(
            input_variables=["context", "question", "conflicting_info"],
            template="""You have encountered conflicting information in the context documents. Analyze the conflicts and provide the most accurate answer.

Context with conflicts:
{context}

Question: {question}

Conflicting information identified:
{conflicting_info}

Provide a balanced answer that:
1. Acknowledges the conflicts
2. Explains different perspectives if they exist
3. Provides the most likely correct answer based on evidence
4. Cites sources for each perspective"""
        )
        
    async def retrieve_context(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from vector store.
        
        Args:
            user_id: User ID for collection access
            query: Search query
            n_results: Number of results to retrieve
            min_score: Minimum similarity score threshold
            
        Returns:
            List of context documents with metadata
        """
        try:
            # Use similarity search to find relevant documents
            results = await self.similarity_search_service.semantic_search(
                user_id=user_id,
                query=query,
                n_results=n_results,
                min_score=min_score
            )
            
            context_docs = []
            for result in results:
                metadata = result.get("metadata", {})
                context_docs.append({
                    "content":     result.get("document", ""),       # ← was "content"
                    "metadata":    metadata,
                    "score":       result.get("score", 0.0),
                    "document_id": metadata.get("document_id"),      # ← was result.get()
                    "chunk_index": metadata.get("chunk_index"),      # ← was result.get()
                    "source":      metadata.get("filename", "Unknown"),  # ← was result.get("source")
                })
            
            logger.info(f"Retrieved {len(context_docs)} context documents for query: {query[:50]}...")
            return context_docs
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def format_context_for_prompt(
        self,
        context_docs: List[Dict[str, Any]],
        max_tokens: int = 2000
    ) -> str:
        """
        Format context documents for inclusion in prompt.
        
        Args:
            context_docs: List of context documents
            max_tokens: Maximum tokens for context (approximate)
            
        Returns:
            Formatted context string
        """
        if not context_docs:
            return "No relevant context found."
        
        formatted_context = []
        total_length = 0
        
        for i, doc in enumerate(context_docs):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            score = doc.get("score", 0.0)
            source = doc.get("source", "Unknown")
            document_id = doc.get("document_id", "Unknown")
            chunk_index = doc.get("chunk_index", 0)
            
            # Format document entry
            entry = f"[Source: {source}, Document: {document_id}, Chunk: {chunk_index}, Relevance: {score:.2f}]\n{content}\n"
            
            # Check if adding this would exceed token limit
            entry_length = len(entry)
            if total_length + entry_length > max_tokens and i > 0:
                break
                
            formatted_context.append(entry)
            total_length += entry_length
        
        return "\n---\n".join(formatted_context)
    
    def format_chat_history_for_prompt(
        self,
        chat_history: List[Dict[str, str]],
        max_messages: int = 10
    ) -> str:
        """
        Format chat history for inclusion in prompt.
        
        Args:
            chat_history: List of messages with 'role' and 'content'
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted chat history string
        """
        if not chat_history:
            return "No previous conversation."
        
        # Take only the most recent messages
        recent_history = chat_history[-max_messages:]
        
        formatted_history = []
        for msg in recent_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted_history.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted_history)
    
    def _select_prompt_template(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Select appropriate prompt template based on query complexity and context.
        
        Args:
            query: User query
            context_docs: Retrieved context documents
            chat_history: Chat history
            
        Returns:
            Selected prompt template
        """
        # Simple heuristics for prompt selection
        query_lower = query.lower()
        
        # Check for complex reasoning indicators
        complex_indicators = [
            "explain", "analyze", "compare", "contrast", "why", "how does",
            "what are the implications", "evaluate", "assess", "discuss"
        ]
        
        # Check for conflicting information in context
        has_conflicts = False
        if len(context_docs) > 1:
            # Simple conflict detection - check for contradictory statements
            # In production, this would be more sophisticated
            content_set = set()
            for doc in context_docs:
                key_phrases = doc.get("content", "")[:100].lower().split()[:10]
                content_set.add(tuple(sorted(key_phrases)))
            
            if len(content_set) < len(context_docs) * 0.5:
                # Potential conflicts if documents are very different
                has_conflicts = True
        
        # Select prompt
        if any(indicator in query_lower for indicator in complex_indicators):
            return self.reasoning_prompt_template.template
        elif has_conflicts and len(context_docs) > 2:
            return self.conflict_resolution_prompt.template
        else:
            return self.rag_prompt_template.template
    
    async def generate_rag_response(
        self,
        user_id: str,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        include_sources: bool = True,
        prompt_strategy: str = "auto"  # auto, basic, reasoning, conflict
    ) -> Dict[str, Any]:
        """
        Generate a RAG-enhanced response.
        
        Args:
            user_id: User ID for context retrieval
            query: User query
            chat_history: Previous conversation messages
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            include_sources: Whether to include source attribution
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Step 1: Retrieve relevant context
            context_docs = await self.retrieve_context(
                user_id=user_id,
                query=query,
                n_results=5,
                min_score=0.3
            )
            
            # Step 2: Format context and chat history for prompt
            formatted_context = self.format_context_for_prompt(context_docs)
            formatted_history = self.format_chat_history_for_prompt(chat_history or [])
            
            # Step 3: Select and prepare prompt
            if prompt_strategy == "auto":
                selected_prompt = self._select_prompt_template(query, context_docs, chat_history)
            elif prompt_strategy == "reasoning":
                selected_prompt = self.reasoning_prompt_template.template
            elif prompt_strategy == "conflict":
                selected_prompt = self.conflict_resolution_prompt.template
            else:
                selected_prompt = self.rag_prompt_template.template
            
            # Prepare the final prompt
            final_prompt = selected_prompt.format(
                context=formatted_context,
                question=query,
                chat_history=formatted_history
            )
            
            # Step 4: Prepare messages for LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert AI assistant that provides accurate, well-reasoned answers based on the provided context. Always cite your sources when using information from the context."
                }
            ]
            
            # Add chat history if available
            if chat_history:
                for msg in chat_history[-10:]:  # Last 10 messages
                    messages.append(msg)
            
            # Add the final prompt as user message
            messages.append({"role": "user", "content": final_prompt})
            
            # Step 4: Generate response using LLM
            llm_response = await self.llm_service.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            response_content = llm_response.get("content", "")
            tokens_used = llm_response.get("tokens_used", 0)
            model_used = llm_response.get("model", model)
            
            # Step 5: Prepare response with source attribution
            # Extract source information
            sources = []
            for doc in context_docs:
                if doc.get("score", 0) >= 0.3:  # Include moderately relevant sources
                    sources.append({
                        "document_id": doc.get("document_id"),
                        "chunk_index": doc.get("chunk_index"),
                        "source": doc.get("source"),
                        "relevance_score": doc.get("score"),
                        "content_preview": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
                    })
            
            # Add citations to response if requested
            if include_sources and sources:
                response_with_citations, formatted_sources = self._add_citations_to_response(
                    response_content,
                    sources,
                    citation_style="numeric"
                )
            else:
                response_with_citations = response_content
                formatted_sources = []
            
            response_data = {
                "content": response_with_citations,
                "model": model_used,
                "tokens_used": tokens_used,
                "context_used": len(context_docs) > 0,
                "context_document_count": len(context_docs),
                "sources": formatted_sources,
                "method": "custom_rag"
            }
            
            logger.info(f"Generated RAG response with {len(context_docs)} context documents, {tokens_used} tokens")
            return response_data
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            # Fall back to basic LLM response
            return await self._fallback_response(
                query=query,
                chat_history=chat_history,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
    
    async def create_langchain_rag_chain(
        self,
        user_id: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        chain_type: str = "stuff"
    ) -> Optional[ConversationalRetrievalChain]:
        """
        Create a LangChain ConversationalRetrievalChain for RAG.
        
        Args:
            user_id: User ID for collection access
            model: LLM model to use
            temperature: Sampling temperature
            chain_type: Chain type (stuff, map_reduce, refine, map_rerank)
            
        Returns:
            LangChain RAG chain or None if creation fails
        """
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain is not available. Cannot create LangChain RAG chain.")
            return None
            
        try:
            from app.core.config import settings
            
            # Initialize LLM
            llm = ChatOpenAI(
                model_name=model or settings.OPENAI_MODEL,
                temperature=temperature,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Initialize embeddings
            embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Connect to ChromaDB
            chroma_client = await self.vector_store._get_client()
            collection_name = self.vector_store._get_collection_name(user_id)
            
            # Create vector store
            vectorstore = Chroma(
                client=chroma_client,
                collection_name=collection_name,
                embedding_function=embeddings
            )
            
            # Create memory for conversation
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            
            # Create RAG chain
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vectorstore.as_retriever(
                    search_kwargs={"k": 5}
                ),
                memory=memory,
                chain_type=chain_type,
                return_source_documents=True,
                verbose=False
            )
            
            logger.info(f"Created LangChain RAG chain for user {user_id}")
            return qa_chain
            
        except Exception as e:
            logger.error(f"Error creating LangChain RAG chain: {e}")
            return None
    
    def _format_citations(
        self,
        sources: List[Dict[str, Any]],
        citation_style: str = "numeric"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Format citations for inclusion in response.
        
        Args:
            sources: List of source documents
            citation_style: Citation style (numeric, author_date, inline)
            
        Returns:
            Tuple of (formatted_citations, detailed_sources)
        """
        if not sources:
            return "", []
        
        detailed_sources = []
        
        if citation_style == "numeric":
            # [1], [2], [3] style citations
            citations = []
            for i, source in enumerate(sources, 1):
                doc_id = source.get("document_id", f"Doc{i}")
                chunk_idx = source.get("chunk_index", 0)
                source_name = source.get("source", "Unknown")
                
                citations.append(f"[{i}]")
                detailed_sources.append({
                    "citation_number": i,
                    "document_id": doc_id,
                    "chunk_index": chunk_idx,
                    "source": source_name,
                    "relevance_score": source.get("relevance_score", 0.0),
                    "content_preview": source.get("content_preview", "")
                })
            
            citation_text = " ".join(citations)
            
        elif citation_style == "author_date":
            # (Author, Year) style citations
            citations = []
            for i, source in enumerate(sources, 1):
                source_name = source.get("source", "Unknown")
                # Extract author/year from source name if possible
                if " - " in source_name:
                    author_part = source_name.split(" - ")[0]
                else:
                    author_part = source_name
                
                citations.append(f"({author_part[:20]})")
                detailed_sources.append({
                    "citation": f"({author_part[:20]})",
                    "document_id": source.get("document_id"),
                    "source": source_name,
                    "relevance_score": source.get("relevance_score", 0.0)
                })
            
            citation_text = " ".join(citations)
            
        else:  # inline style
            # Include source names inline
            source_names = []
            for source in sources:
                source_name = source.get("source", "Unknown")
                if source_name not in source_names:
                    source_names.append(source_name)
                
                detailed_sources.append({
                    "source": source_name,
                    "document_id": source.get("document_id"),
                    "chunk_index": source.get("chunk_index", 0),
                    "relevance_score": source.get("relevance_score", 0.0)
                })
            
            citation_text = f"Sources: {', '.join(source_names[:3])}"
            if len(source_names) > 3:
                citation_text += f" and {len(source_names) - 3} more"
        
        return citation_text, detailed_sources
    
    def _add_citations_to_response(
        self,
        response_text: str,
        sources: List[Dict[str, Any]],
        citation_style: str = "numeric"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Add citations to response text.
        
        Args:
            response_text: Original response text
            sources: Source documents
            citation_style: Citation style to use
            
        Returns:
            Tuple of (response_with_citations, formatted_sources)
        """
        if not sources:
            return response_text, []
        
        # Format citations
        citation_text, formatted_sources = self._format_citations(sources, citation_style)
        
        # Add citations to response
        if citation_style == "numeric":
            # Add citation markers in text (simplified - in production would be more sophisticated)
            response_with_citations = response_text + f"\n\n**References:** {citation_text}"
        else:
            response_with_citations = response_text + f"\n\n{citation_text}"
        
        return response_with_citations, formatted_sources
    
    async def generate_with_langchain(
        self,
        user_id: str,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate response using LangChain RAG chain.
        
        Args:
            user_id: User ID
            query: User query
            chat_history: Previous conversation messages
            model: LLM model to use
            temperature: Sampling temperature
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Create or get cached chain
            chain = await self.create_langchain_rag_chain(
                user_id=user_id,
                model=model,
                temperature=temperature
            )
            
            if not chain:
                raise RuntimeError("Failed to create LangChain RAG chain")
            
            # Prepare chat history for LangChain
            if chat_history:
                # Convert to LangChain message format
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == "user":
                        chain.memory.chat_memory.add_user_message(content)
                    elif role == "assistant":
                        chain.memory.chat_memory.add_ai_message(content)
            
            # Generate response
            result = await chain.acall({"question": query})
            
            # Extract source documents
            source_docs = result.get("source_documents", [])
            sources = []
            
            for doc in source_docs:
                metadata = doc.metadata
                sources.append({
                    "document_id": metadata.get("document_id", "Unknown"),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "source": metadata.get("source", "Unknown"),
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            
            return {
                "content": result.get("answer", ""),
                "model": model,
                "tokens_used": None,  # LangChain doesn't provide token count directly
                "context_used": len(source_docs) > 0,
                "context_document_count": len(source_docs),
                "sources": sources,
                "method": "langchain"
            }
            
        except Exception as e:
            logger.error(f"Error generating with LangChain: {e}")
            # Fall back to custom RAG implementation
            return await self.generate_rag_response(
                user_id=user_id,
                query=query,
                chat_history=chat_history,
                model=model,
                temperature=temperature,
                prompt_strategy="basic"
            )
    
    async def _fallback_response(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Fallback to basic LLM response when RAG fails.
        
        Args:
            query: User query
            chat_history: Previous conversation messages
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."}
            ]
            
            if chat_history:
                for msg in chat_history[-10:]:
                    messages.append(msg)
            
            messages.append({"role": "user", "content": query})
            
            llm_response = await self.llm_service.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            return {
                "content": llm_response.get("content", ""),
                "model": llm_response.get("model", model),
                "tokens_used": llm_response.get("tokens_used", 0),
                "context_used": False,
                "context_document_count": 0,
                "sources": []
            }
            
        except Exception as e:
            logger.error(f"Error in fallback response: {e}")
            return {
                "content": "I apologize, but I'm having trouble processing your request. Please try again.",
                "model": model,
                "tokens_used": 0,
                "context_used": False,
                "context_document_count": 0,
                "sources": []
            }


# Global instance for easy import
rag_service = RAGService()