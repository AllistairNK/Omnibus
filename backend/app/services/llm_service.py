"""
LLM service with multi-model support and provider abstraction.

This service provides a unified interface for multiple LLM providers
(OpenAI, Anthropic, Google Gemini) with fallback logic.
"""
import logging
from typing import AsyncGenerator, Dict, List, Optional, Any

from app.core.config import settings
from app.services.llm_provider import (
    LLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    LLMProviderType,
)

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service with multi-provider support and fallback logic."""
    
    def __init__(self) -> None:
        """Initialize LLM service with multiple providers."""
        self.providers: Dict[LLMProviderType, LLMProvider] = {}
        self.default_provider_type: Optional[LLMProviderType] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize all available providers."""
        # Initialize OpenAI provider if API key is set
        if settings.OPENAI_API_KEY:
            try:
                openai_provider = OpenAIProvider(
                    api_key=settings.OPENAI_API_KEY,
                    default_model=settings.OPENAI_MODEL,
                )
                await openai_provider.initialize()
                self.providers[LLMProviderType.OPENAI] = openai_provider
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI provider: {e}")
        
        # Initialize Anthropic provider if API key is set
        if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
            try:
                anthropic_provider = AnthropicProvider(
                    api_key=settings.ANTHROPIC_API_KEY,
                    default_model=getattr(settings, 'ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
                )
                await anthropic_provider.initialize()
                self.providers[LLMProviderType.ANTHROPIC] = anthropic_provider
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic provider: {e}")
        
        # Initialize Gemini provider if API key is set
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            try:
                gemini_provider = GeminiProvider(
                    api_key=settings.GEMINI_API_KEY,
                    default_model=getattr(settings, 'GEMINI_MODEL', 'gemini-pro'),
                )
                await gemini_provider.initialize()
                self.providers[LLMProviderType.GEMINI] = gemini_provider
                logger.info("Gemini provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini provider: {e}")
        
        # Set default provider based on configuration and availability
        if self.providers:
            # Try to use configured default provider
            configured_default = getattr(settings, 'DEFAULT_LLM_PROVIDER', 'openai').lower()
            try:
                configured_type = LLMProviderType(configured_default)
                if configured_type in self.providers:
                    self.default_provider_type = configured_type
                    logger.info(f"Using configured default provider: {configured_type}")
                else:
                    # Fallback to first available provider
                    self.default_provider_type = list(self.providers.keys())[0]
                    logger.warning(f"Configured provider {configured_type} not available, using {self.default_provider_type}")
            except ValueError:
                # Invalid provider type in config
                self.default_provider_type = list(self.providers.keys())[0]
                logger.warning(f"Invalid DEFAULT_LLM_PROVIDER '{configured_default}', using {self.default_provider_type}")
            
            self._initialized = True
            logger.info(f"LLM service initialized with {len(self.providers)} provider(s), default: {self.default_provider_type}")
        else:
            logger.warning("No LLM providers available. LLM service disabled.")
    
    async def is_available(self) -> bool:
        """Check if any LLM provider is available."""
        return self._initialized and len(self.providers) > 0
    
    def get_available_providers(self) -> List[LLMProviderType]:
        """Get list of available provider types."""
        return list(self.providers.keys())
    
    def get_provider(self, provider_type: Optional[LLMProviderType] = None) -> Optional[LLMProvider]:
        """
        Get provider instance by type.
        
        Args:
            provider_type: Provider type to get. If None, returns default provider.
            
        Returns:
            Provider instance or None if not available.
        """
        if not self.providers:
            return None
            
        if provider_type is None:
            provider_type = self.default_provider_type
            
        return self.providers.get(provider_type)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        provider_type: Optional[LLMProviderType] = None,
        fallback: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate chat completion using specified or default provider with fallback.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (provider-specific)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            provider_type: Specific provider to use (None for default)
            fallback: Whether to try other providers if the requested one fails
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary with completion data
            
        Raises:
            RuntimeError: If no providers are available
        """
        if not await self.is_available():
            raise RuntimeError("No LLM providers available")
        
        # Determine which providers to try
        providers_to_try = []
        
        if provider_type is not None:
            # Try requested provider first
            providers_to_try.append(provider_type)
            
            # Add fallback providers if enabled
            if fallback:
                for other_type in self.providers.keys():
                    if other_type != provider_type:
                        providers_to_try.append(other_type)
        else:
            # Use default provider and all others as fallbacks
            providers_to_try = list(self.providers.keys())
        
        last_error = None
        
        for provider_type_to_try in providers_to_try:
            provider = self.providers.get(provider_type_to_try)
            if not provider or not await provider.is_available():
                continue
                
            try:
                result = await provider.chat_completion(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    **kwargs,
                )
                
                # Add provider info to result
                result["provider_used"] = provider_type_to_try.value
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_type_to_try} failed: {e}. Trying next provider...")
                continue
        
        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        provider_type: Optional[LLMProviderType] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion tokens from specified provider.
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            provider_type: Specific provider to use (None for default)
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Token chunks from the stream
            
        Raises:
            RuntimeError: If provider is not available
        """
        if not await self.is_available():
            raise RuntimeError("No LLM providers available")
        
        provider = self.get_provider(provider_type)
        if not provider or not await provider.is_available():
            raise RuntimeError(f"Requested provider {provider_type} not available")
        
        # Clear previous usage
        self._last_stream_usage = None
        
        try:
            async for chunk in provider.chat_completion_stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            ):
                yield chunk
            
            # After streaming completes, retrieve usage data from provider
            # Check if provider has a method to get stream usage
            if hasattr(provider, 'get_stream_usage'):
                usage = provider.get_stream_usage()
                if usage:
                    self._last_stream_usage = usage
        except Exception as e:
            logger.error(f"Error in chat completion streaming: {e}")
            raise
    
    def get_last_stream_usage(self) -> Optional[Dict[str, Any]]:
        """Get usage data from the last streaming completion.
        
        Returns:
            Dict with usage statistics if available, None otherwise.
            Structure depends on provider (e.g., OpenAI: prompt_tokens, completion_tokens, total_tokens).
        """
        return getattr(self, '_last_stream_usage', None)
    
    async def count_tokens(
        self,
        text: str,
        model: Optional[str] = None,
        provider_type: Optional[LLMProviderType] = None,
    ) -> int:
        """
        Estimate token count for text using specified provider.
        
        Args:
            text: Text to count tokens for
            model: Model to use for tokenization
            provider_type: Provider to use for token counting
            
        Returns:
            Estimated token count
        """
        if not await self.is_available():
            return len(text) // 4  # Fallback estimation
        
        provider = self.get_provider(provider_type)
        if not provider or not await provider.is_available():
            return len(text) // 4  # Fallback estimation
        
        return await provider.count_tokens(text, model)
    
    def get_supported_models(self, provider_type: Optional[LLMProviderType] = None) -> Dict[str, List[str]]:
        """
        Get supported models for all or specific providers.
        
        Args:
            provider_type: Provider to get models for (None for all)
            
        Returns:
            Dictionary mapping provider types to list of supported models
        """
        result = {}
        
        if provider_type is not None:
            provider = self.providers.get(provider_type)
            if provider:
                result[provider_type.value] = provider.get_supported_models()
        else:
            for p_type, provider in self.providers.items():
                result[p_type.value] = provider.get_supported_models()
        
        return result


# Global LLM service instance
llm_service = LLMService()


async def get_llm_service() -> LLMService:
    """Get LLM service instance for dependency injection."""
    return llm_service