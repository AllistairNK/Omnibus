"""
LLM service for basic chat completion without RAG.
"""
import logging
from typing import AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service for chat completion."""
    
    def __init__(self) -> None:
        """Initialize LLM service."""
        self._client: Optional[AsyncOpenAI] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set, LLM service disabled")
            return
            
        try:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self._initialized = True
            logger.info("LLM service initialized with OpenAI")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self._initialized and self._client is not None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
    ) -> Dict[str, any]:
        """
        Generate chat completion using OpenAI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to settings.OPENAI_MODEL)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Dictionary with completion data
        """
        if not await self.is_available():
            raise RuntimeError("LLM service not available")
        
        try:
            model_to_use = model or settings.OPENAI_MODEL
            
            if stream:
                # For streaming, we return the stream object
                response = await self._client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                return {"stream": response}
            else:
                # For non-streaming, get full response
                response = await self._client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                
                completion = response.choices[0].message
                usage = response.usage
                
                return {
                    "content": completion.content,
                    "role": completion.role,
                    "model": model_to_use,
                    "tokens_used": usage.total_tokens if usage else None,
                    "finish_reason": response.choices[0].finish_reason,
                }
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion tokens.
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Token chunks from the stream
        """
        if not await self.is_available():
            raise RuntimeError("LLM service not available")
        
        try:
            model_to_use = model or settings.OPENAI_MODEL
            
            response = await self._client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except OpenAIError as e:
            logger.error(f"OpenAI API error during streaming: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in chat completion streaming: {e}")
            raise
    
    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Estimate token count for text.
        
        Note: This is a rough estimation. For accurate counts, use tiktoken.
        
        Args:
            text: Text to count tokens for
            model: Model to use for tokenization
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token for English text
        # In production, you would use tiktoken or similar
        return len(text) // 4


# Global LLM service instance
llm_service = LLMService()


async def get_llm_service() -> LLMService:
    """Get LLM service instance for dependency injection."""
    return llm_service