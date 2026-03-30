"""
Embedding generation service for creating vector embeddings from text.

Supports multiple embedding providers (OpenAI, local models) with a unified interface.
"""

import logging
from typing import List, Optional
from abc import ABC, abstractmethod

import httpx
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings from this provider."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding models."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            model: OpenAI embedding model (defaults to settings.OPENAI_EMBEDDING_MODEL)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=30.0,  # Add this — stops it hanging forever
            max_retries=1
            )
        
        # Model dimension mapping
        self._model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured")
        
        try:
            # OpenAI client is synchronous, so we run in thread pool
            import asyncio
            from functools import partial
            
            loop = asyncio.get_running_loop()
            generate_fn = partial(
                self.client.embeddings.create,
                model=self.model,
                input=texts
            )
            
            response = await loop.run_in_executor(None, generate_fn)
            
            # Extract embeddings in the same order as input texts
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate OpenAI embeddings: {e}")
            raise
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions for the configured model."""
        return self._model_dimensions.get(self.model, 1536)


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding provider using sentence-transformers or similar.
    
    Note: This is a placeholder implementation. In production, you would
    load a local model like sentence-transformers/all-MiniLM-L6-v2
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding provider.
        
        Args:
            model_name: Name of the local model to use
        """
        self.model_name = model_name
        self.model = None
        self._dimensions = 384  # Default for all-MiniLM-L6-v2
    
    async def _load_model(self):
        """Lazy load the embedding model."""
        if self.model is None:
            try:
                # Import here to avoid dependency if not using local embeddings
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                # Get actual dimensions from model
                test_embedding = self.model.encode(["test"])
                self._dimensions = len(test_embedding[0])
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
                raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        await self._load_model()
        
        try:
            # sentence-transformers is synchronous
            import asyncio
            from functools import partial
            
            loop = asyncio.get_running_loop()
            encode_fn = partial(self.model.encode, texts, convert_to_numpy=True)
            
            embeddings = await loop.run_in_executor(None, encode_fn)
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate local embeddings: {e}")
            raise
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions


class EmbeddingService:
    """Main embedding service that manages multiple providers."""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize embedding service.
        
        Args:
            provider: Embedding provider to use ("openai", "local", or None for auto)
        """
        self.provider_name = provider or "openai"
        self._provider = None
    
    async def get_provider(self) -> EmbeddingProvider:
        """Get or create the embedding provider instance."""
        if self._provider is not None:
            return self._provider
        
        if self.provider_name == "openai":
            self._provider = OpenAIEmbeddingProvider()
        elif self.provider_name == "local":
            self._provider = LocalEmbeddingProvider()
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider_name}")
        
        return self._provider
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using the configured provider."""
        provider = await self.get_provider()
        return await provider.generate_embeddings(texts)
    
    async def get_embedding_dimensions(self) -> int:
        """Get the dimensionality of embeddings from the current provider."""
        provider = await self.get_provider()
        return provider.get_dimensions()
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]


# Global instance for easy access
embedding_service = EmbeddingService()