"""
LLM Provider Abstraction Layer.

This module defines the base interface for LLM providers and concrete implementations
for OpenAI, Anthropic, and Google Gemini.
"""
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProviderType(str, Enum):
    """Enumeration of supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    # Add more providers as needed


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available."""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary with completion data
        """
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion tokens.
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Token chunks from the stream
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
            model: Model to use for tokenization
            
        Returns:
            Estimated token count
        """
        pass
    
    @abstractmethod
    def get_provider_type(self) -> LLMProviderType:
        """Get the provider type."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of supported models for this provider."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation."""
    
    def __init__(self, api_key: str, default_model: str = "gpt-5-nano"):
        """Initialize OpenAI provider."""
        self.api_key = api_key
        self.default_model = default_model
        self._client = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set, OpenAI provider disabled")
            return
            
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
            self._initialized = True
            logger.info("OpenAI provider initialized")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return self._initialized and self._client is not None
    
    async def _create_openai_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs: Any,
    ):
        """
        Create OpenAI chat completion with fallback for max_tokens vs max_completion_tokens.
        
        Some newer OpenAI models (e.g., gpt-5-nano) require max_completion_tokens instead of max_tokens.
        This method attempts with max_tokens first, and if that fails with the specific unsupported
        parameter error, retries with max_completion_tokens.
        """
        from openai import BadRequestError
        # Models that only support default temperature (1)
        FIXED_TEMPERATURE_MODELS = {
            "o1", "o1-mini", "o3", "o3-mini", "o4-mini",
            "gpt-5-nano", "gpt-5-mini",
            "gpt-5.4-nano", "gpt-5.4-mini",
        }

        base_params = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs,
        }

        # Omit temperature entirely for models that don't support it
        if model not in FIXED_TEMPERATURE_MODELS:
            base_params["temperature"] = temperature

        try:
            return await self._client.chat.completions.create(
                **base_params,
                max_tokens=max_tokens,
            )
        except BadRequestError as e:
            if (
                hasattr(e, "code") and e.code == "unsupported_parameter"
                and hasattr(e, "param") and e.param == "max_tokens"
            ):
                return await self._client.chat.completions.create(
                    **base_params,
                    max_completion_tokens=max_tokens,
                )
            # Also catch temperature errors at runtime for unknown new models
            elif (
                hasattr(e, "param") and e.param == "temperature"
            ):
                base_params.pop("temperature", None)
                return await self._client.chat.completions.create(
                    **base_params,
                    max_tokens=max_tokens,
                )
            else:
                raise
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate chat completion using OpenAI."""
        if not await self.is_available():
            raise RuntimeError("OpenAI provider not available")
            
        try:
            from openai import OpenAIError
            
            model_to_use = model or self.default_model
            
            response = await self._create_openai_chat_completion(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )
            
            if stream:
                return {"stream": response}
            else:
                completion = response.choices[0].message
                usage = response.usage
                
                return {
                    "content": completion.content,
                    "role": completion.role,
                    "model": model_to_use,
                    "tokens_used": usage.total_tokens if usage else None,
                    "finish_reason": response.choices[0].finish_reason,
                    "provider": "openai",
                }
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in OpenAI chat completion: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion tokens from OpenAI."""
        if not await self.is_available():
            raise RuntimeError("OpenAI provider not available")
            
        try:
            from openai import OpenAIError
            
            model_to_use = model or self.default_model
            
            response = await self._create_openai_chat_completion(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except OpenAIError as e:
            logger.error(f"OpenAI API error during streaming: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in OpenAI chat completion streaming: {e}")
            raise
    
    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Estimate token count for text using tiktoken if available."""
        try:
            import tiktoken
            model_to_use = model or self.default_model
            
            # Try to get encoding for the model
            try:
                encoding = tiktoken.encoding_for_model(model_to_use)
            except KeyError:
                # Fallback to cl100k_base which works for most OpenAI models
                encoding = tiktoken.get_encoding("cl100k_base")
                
            return len(encoding.encode(text))
        except ImportError:
            # Fallback to rough estimation if tiktoken not available
            logger.warning("tiktoken not installed, using rough token estimation")
            return len(text) // 4
    
    def get_provider_type(self) -> LLMProviderType:
        """Get the provider type."""
        return LLMProviderType.OPENAI
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported OpenAI models."""
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-5-nano"
        ]


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self, api_key: str, default_model: str = "claude-3-haiku-20240307"):
        """Initialize Anthropic provider."""
        self.api_key = api_key
        self.default_model = default_model
        self._client = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize Anthropic client."""
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set, Anthropic provider disabled")
            return
            
        try:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            self._initialized = True
            logger.info("Anthropic provider initialized")
        except ImportError:
            logger.error("Anthropic package not installed. Install with: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if Anthropic provider is available."""
        return self._initialized and self._client is not None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate chat completion using Anthropic Claude."""
        if not await self.is_available():
            raise RuntimeError("Anthropic provider not available")
            
        try:
            model_to_use = model or self.default_model
            
            # Convert messages to Anthropic format
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            if stream:
                response = await self._client.messages.create(
                    model=model_to_use,
                    messages=anthropic_messages,
                    system=system_message,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs,
                )
                return {"stream": response}
            else:
                response = await self._client.messages.create(
                    model=model_to_use,
                    messages=anthropic_messages,
                    system=system_message,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                    **kwargs,
                )
                
                # Extract content from response
                content = ""
                for content_block in response.content:
                    if content_block.type == "text":
                        content += content_block.text
                
                return {
                    "content": content,
                    "role": "assistant",
                    "model": model_to_use,
                    "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                    "finish_reason": response.stop_reason,
                    "provider": "anthropic",
                }
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion tokens from Anthropic."""
        if not await self.is_available():
            raise RuntimeError("Anthropic provider not available")
            
        try:
            model_to_use = model or self.default_model
            
            # Convert messages to Anthropic format
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            response = await self._client.messages.create(
                model=model_to_use,
                messages=anthropic_messages,
                system=system_message,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )
            
            async for chunk in response:
                if chunk.type == "content_block_delta":
                    if chunk.delta.type == "text_delta":
                        yield chunk.delta.text
        except Exception as e:
            logger.error(f"Anthropic API error during streaming: {e}")
            raise
    
    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Estimate token count for text using Anthropic's tokenizer if available."""
        try:
            # Anthropic doesn't have a public tokenizer, use rough estimation
            # In production, you might want to use a different approach
            return len(text) // 4
        except Exception:
            # Fallback to rough estimation
            return len(text) // 4
    
    def get_provider_type(self) -> LLMProviderType:
        """Get the provider type."""
        return LLMProviderType.ANTHROPIC
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported Anthropic models."""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""
    
    def __init__(self, api_key: str, default_model: str = "gemini-pro"):
        """Initialize Gemini provider."""
        self.api_key = api_key
        self.default_model = default_model
        self._client = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize Gemini client."""
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set, Gemini provider disabled")
            return
            
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai
            self._initialized = True
            logger.info("Gemini provider initialized")
        except ImportError:
            logger.error("Google Generative AI package not installed. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini provider: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if Gemini provider is available."""
        return self._initialized and self._client is not None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate chat completion using Google Gemini."""
        if not await self.is_available():
            raise RuntimeError("Gemini provider not available")
            
        try:
            import google.generativeai as genai
            
            model_to_use = model or self.default_model
            
            # Convert messages to Gemini format
            system_instruction = None
            gemini_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    # Gemini uses 'user' and 'model' roles
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_messages.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })
            
            # Create the model with configuration
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                **kwargs,
            }
            
            gemini_model = genai.GenerativeModel(
                model_name=model_to_use,
                generation_config=generation_config,
                system_instruction=system_instruction,
            )
            
            # Start a chat session
            chat = gemini_model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
            
            # Get the last message (user's message)
            last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""
            
            if stream:
                response = chat.send_message(last_message, stream=True)
                return {"stream": response}
            else:
                response = chat.send_message(last_message, stream=False)
                
                return {
                    "content": response.text,
                    "role": "model",
                    "model": model_to_use,
                    "tokens_used": None,  # Gemini doesn't provide token usage in free tier
                    "finish_reason": response.candidates[0].finish_reason if response.candidates else None,
                    "provider": "gemini",
                }
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion tokens from Gemini."""
        if not await self.is_available():
            raise RuntimeError("Gemini provider not available")
            
        try:
            import google.generativeai as genai
            
            model_to_use = model or self.default_model
            
            # Convert messages to Gemini format
            system_instruction = None
            gemini_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_messages.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                **kwargs,
            }
            
            gemini_model = genai.GenerativeModel(
                model_name=model_to_use,
                generation_config=generation_config,
                system_instruction=system_instruction,
            )
            
            chat = gemini_model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
            last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""
            
            response = chat.send_message(last_message, stream=True)
            
            for chunk in response:
                yield chunk.text
        except Exception as e:
            logger.error(f"Gemini API error during streaming: {e}")
            raise
    
    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Estimate token count for text."""
        # Gemini doesn't have a public tokenizer, use rough estimation
        return len(text) // 4
    
    def get_provider_type(self) -> LLMProviderType:
        """Get the provider type."""
        return LLMProviderType.GEMINI
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported Gemini models."""
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-ultra",
        ]