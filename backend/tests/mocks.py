"""
Mocking utilities for external services.
"""
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional, List
import uuid

from tests.factories import create_mock_supabase_response, create_mock_supabase_auth_response


class MockOpenAI:
    """Mock OpenAI client for testing."""
    
    def __init__(self):
        self.chat = MagicMock()
        self.completions = MagicMock()
        self.embeddings = MagicMock()
        self.models = MagicMock()
        
        # Setup default mock responses
        self.setup_default_mocks()
    
    def setup_default_mocks(self):
        """Setup default mock responses for OpenAI."""
        # Mock chat completion
        mock_chat_response = MagicMock()
        mock_chat_response.choices = [MagicMock()]
        mock_chat_response.choices[0].message = MagicMock()
        mock_chat_response.choices[0].message.content = "Mock AI response"
        mock_chat_response.usage = MagicMock()
        mock_chat_response.usage.total_tokens = 100
        
        self.chat.completions.create = AsyncMock(return_value=mock_chat_response)
        
        # Mock embeddings
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock()]
        mock_embedding_response.data[0].embedding = [0.1] * 1536  # OpenAI embedding dimension
        mock_embedding_response.usage = MagicMock()
        mock_embedding_response.usage.total_tokens = 10
        
        self.embeddings.create = AsyncMock(return_value=mock_embedding_response)
        
        # Mock models list
        mock_models_response = MagicMock()
        mock_models_response.data = [
            MagicMock(id="gpt-5-nano", object="model"),
            MagicMock(id="gpt-3.5-turbo", object="model"),
        ]
        self.models.list = AsyncMock(return_value=mock_models_response)


class MockChromaDB:
    """Mock ChromaDB client for testing."""
    
    def __init__(self):
        self.collections = MagicMock()
        self._collections = {}
        
        # Setup default mock collection
        self.setup_default_mocks()
    
    def setup_default_mocks(self):
        """Setup default mock responses for ChromaDB."""
        mock_collection = MagicMock()
        mock_collection.name = "test_collection"
        mock_collection.count = AsyncMock(return_value=10)
        mock_collection.add = AsyncMock()
        mock_collection.query = AsyncMock(return_value={
            "documents": [["Mock document content"]],
            "metadatas": [[{"source": "test.pdf", "page": 1}]],
            "distances": [[0.1]],
            "ids": [[str(uuid.uuid4())]]
        })
        mock_collection.get = AsyncMock(return_value={
            "ids": [str(uuid.uuid4())],
            "documents": ["Mock document"],
            "metadatas": [{"source": "test.pdf"}]
        })
        mock_collection.delete = AsyncMock()
        mock_collection.update = AsyncMock()
        
        self.collections.get_or_create = AsyncMock(return_value=mock_collection)
        self.collections.get = AsyncMock(return_value=mock_collection)
        self.collections.create = AsyncMock(return_value=mock_collection)
        self._collections["test_collection"] = mock_collection


class MockLangChain:
    """Mock LangChain components for testing."""
    
    def __init__(self):
        self.llm_chain = MagicMock()
        self.retriever = MagicMock()
        self.vectorstore = MagicMock()
        
        self.setup_default_mocks()
    
    def setup_default_mocks(self):
        """Setup default mock responses for LangChain."""
        # Mock LLM chain
        mock_llm_response = MagicMock()
        mock_llm_response.content = "Mock LangChain response"
        
        self.llm_chain.invoke = AsyncMock(return_value=mock_llm_response)
        self.llm_chain.arun = AsyncMock(return_value="Mock LangChain response")
        
        # Mock retriever
        mock_document = MagicMock()
        mock_document.page_content = "Mock retrieved content"
        mock_document.metadata = {"source": "test.pdf", "page": 1}
        
        self.retriever.get_relevant_documents = AsyncMock(return_value=[mock_document])
        self.retriever.ainvoke = AsyncMock(return_value=[mock_document])
        
        # Mock vectorstore
        self.vectorstore.similarity_search = AsyncMock(return_value=[mock_document])
        self.vectorstore.add_texts = AsyncMock(return_value=[str(uuid.uuid4())])


def mock_supabase_client(
    auth_response: Optional[Dict[str, Any]] = None,
    table_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    storage_response: Optional[Dict[str, Any]] = None,
) -> MagicMock:
    """
    Create a mock Supabase client with configurable responses.
    
    Args:
        auth_response: Mock auth response configuration
        table_data: Mock table data keyed by table name
        storage_response: Mock storage response configuration
    
    Returns:
        Mock Supabase client
    """
    mock_client = MagicMock()
    
    # Mock auth
    mock_client.auth = MagicMock()
    
    if auth_response:
        mock_client.auth.sign_up = AsyncMock(return_value=auth_response.get("sign_up"))
        mock_client.auth.sign_in_with_password = AsyncMock(return_value=auth_response.get("sign_in"))
        mock_client.auth.sign_out = AsyncMock(return_value=auth_response.get("sign_out"))
        mock_client.auth.get_user = AsyncMock(return_value=auth_response.get("get_user"))
        mock_client.auth.reset_password_for_email = AsyncMock(return_value=auth_response.get("reset_password"))
        mock_client.auth.update_user = AsyncMock(return_value=auth_response.get("update_user"))
    else:
        # Default auth mocks
        default_user = {"id": str(uuid.uuid4()), "email": "test@example.com"}
        default_session = {"access_token": "mock_token", "refresh_token": "mock_refresh"}
        
        mock_client.auth.sign_up = AsyncMock(return_value=create_mock_supabase_auth_response(
            user=default_user, session=default_session
        ))
        mock_client.auth.sign_in_with_password = AsyncMock(return_value=create_mock_supabase_auth_response(
            user=default_user, session=default_session
        ))
        mock_client.auth.sign_out = AsyncMock()
        mock_client.auth.get_user = AsyncMock(return_value=MagicMock(user=MagicMock(id=default_user["id"])))
        mock_client.auth.reset_password_for_email = AsyncMock()
        mock_client.auth.update_user = AsyncMock(return_value=MagicMock(user=MagicMock(id=default_user["id"])))
    
    # Mock storage
    mock_client.storage = MagicMock()
    mock_storage_from = MagicMock()
    mock_client.storage.from_ = MagicMock(return_value=mock_storage_from)
    
    if storage_response:
        mock_storage_from.upload = AsyncMock(return_value=storage_response.get("upload"))
        mock_storage_from.get_public_url = AsyncMock(return_value=storage_response.get("get_public_url"))
        mock_storage_from.remove = AsyncMock(return_value=storage_response.get("remove"))
    else:
        mock_storage_from.upload = AsyncMock(return_value=MagicMock())
        mock_storage_from.get_public_url = AsyncMock(return_value="https://example.com/file.pdf")
        mock_storage_from.remove = AsyncMock()
    
    # Mock table operations
    mock_client.table = MagicMock()
    
    def create_table_mock(table_name: str) -> MagicMock:
        """Create a mock for a specific table."""
        mock_table = MagicMock()
        
        # Get data for this table
        data = (table_data or {}).get(table_name, [])
        
        # Mock query builder methods
        mock_table.select = MagicMock(return_value=mock_table)
        mock_table.insert = MagicMock(return_value=mock_table)
        mock_table.update = MagicMock(return_value=mock_table)
        mock_table.delete = MagicMock(return_value=mock_table)
        mock_table.eq = MagicMock(return_value=mock_table)
        mock_table.order = MagicMock(return_value=mock_table)
        
        # Mock execute to return appropriate data
        mock_table.execute = AsyncMock(return_value=create_mock_supabase_response(data=data))
        
        return mock_table
    
    mock_client.table.side_effect = create_table_mock
    
    return mock_client


def patch_external_services(
    mock_openai: bool = True,
    mock_chromadb: bool = True,
    mock_langchain: bool = True,
    mock_supabase: bool = True,
):
    """
    Context manager to patch external services for testing.
    
    Args:
        mock_openai: Whether to mock OpenAI
        mock_chromadb: Whether to mock ChromaDB
        mock_langchain: Whether to mock LangChain
        mock_supabase: Whether to mock Supabase
    
    Returns:
        Context manager with mocked services
    """
    patches = []
    
    if mock_openai:
        patches.append(patch("openai.AsyncOpenAI", return_value=MockOpenAI()))
    
    if mock_chromadb:
        patches.append(patch("chromadb.AsyncHttpClient", return_value=MockChromaDB()))
        patches.append(patch("chromadb.Client", return_value=MockChromaDB()))
    
    if mock_langchain:
        patches.append(patch("langchain.chat_models.ChatOpenAI", return_value=MagicMock()))
        patches.append(patch("langchain.embeddings.OpenAIEmbeddings", return_value=MagicMock()))
    
    if mock_supabase:
        patches.append(patch("supabase.create_client", return_value=mock_supabase_client()))
    
    class MockContext:
        def __init__(self, patches):
            self.patches = patches
            self.mocks = {}
        
        def __enter__(self):
            for patch_obj in self.patches:
                mock = patch_obj.start()
                # Store the mock by its target
                self.mocks[patch_obj.getter()] = mock
            return self.mocks
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            for patch_obj in self.patches:
                patch_obj.stop()
    
    return MockContext(patches)