# =============================================================================
# LLM Provider Abstraction Layer
# =============================================================================
# Unified interface for multiple LLM providers with fallback support
# =============================================================================

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from functools import lru_cache

import structlog
from pydantic import BaseModel

from shared.config.settings import settings

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMMessage(BaseModel):
    """Represents a message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, default_model: str):
        self.api_key = api_key
        self.default_model = default_model
        self.logger = structlog.get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Type[T]] = None,
    ) -> tuple[str, int]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            model: Model to use (defaults to provider default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            response_format: Optional Pydantic model for structured output
            
        Returns:
            Tuple of (response_text, tokens_used)
        """
        pass
    
    @abstractmethod
    async def generate_chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> tuple[str, int]:
        """
        Generate a response from a chat conversation.
        
        Args:
            messages: List of conversation messages
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Tuple of (response_text, tokens_used)
        """
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding floats
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        default_model: str = "gpt-4-turbo-preview"
    ):
        super().__init__(
            api_key=api_key or settings.llm.openai_api_key,
            default_model=default_model
        )
        self.api_base = api_base or settings.llm.openai_api_base
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            kwargs = {"api_key": self.api_key}
            if self.api_base:
                kwargs["base_url"] = self.api_base
            self._client = AsyncOpenAI(**kwargs)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Type[T]] = None,
    ) -> tuple[str, int]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add JSON mode if structured output requested
        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.client.chat.completions.create(**kwargs)
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        
        self.logger.debug(
            "OpenAI generation complete",
            model=kwargs["model"],
            tokens=tokens
        )
        
        return content, tokens
    
    async def generate_chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> tuple[str, int]:
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        
        return content, tokens
    
    async def embed(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "claude-3-sonnet-20240229"
    ):
        super().__init__(
            api_key=api_key or settings.llm.anthropic_api_key,
            default_model=default_model
        )
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Type[T]] = None,
    ) -> tuple[str, int]:
        kwargs = {
            "model": model or self.default_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        # Anthropic doesn't have native JSON mode, but we can instruct it
        if response_format:
            kwargs["messages"][0]["content"] += "\n\nRespond with valid JSON only."
        
        response = await self.client.messages.create(**kwargs)
        
        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        
        self.logger.debug(
            "Anthropic generation complete",
            model=kwargs["model"],
            tokens=tokens
        )
        
        return content, tokens
    
    async def generate_chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> tuple[str, int]:
        # Separate system message from conversation
        system_prompt = None
        conversation = []
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                conversation.append({"role": msg.role, "content": msg.content})
        
        kwargs = {
            "model": model or self.default_model,
            "max_tokens": max_tokens,
            "messages": conversation,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = await self.client.messages.create(**kwargs)
        
        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        
        return content, tokens
    
    async def embed(self, text: str) -> List[float]:
        # Anthropic doesn't have embeddings API, fall back to OpenAI
        openai_provider = OpenAIProvider()
        return await openai_provider.embed(text)


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gemini-2.5-flash"
    ):
        super().__init__(
            api_key=api_key or settings.llm.gemini_api_key,
            default_model=default_model
        )
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Type[T]] = None,
    ) -> tuple[str, int]:
        model_name = model or self.default_model
        gen_model = self.client.GenerativeModel(model_name)
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        if response_format:
            full_prompt += "\n\nRespond with valid JSON only."
        
        # Run in executor since google-generativeai is sync
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: gen_model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
        )
        
        content = response.text
        # Gemini doesn't provide token counts in the same way
        tokens = len(prompt.split()) + len(content.split())  # Rough estimate
        
        self.logger.debug(
            "Gemini generation complete",
            model=model_name,
            tokens=tokens
        )
        
        return content, tokens
    
    async def generate_chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> tuple[str, int]:
        # Convert to single prompt for Gemini
        prompt_parts = []
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        
        prompt_parts.append("Assistant:")
        full_prompt = "\n\n".join(prompt_parts)
        
        return await self.generate(
            prompt=full_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def embed(self, text: str) -> List[float]:
        # Use Gemini's embedding model
        model = self.client.GenerativeModel("models/embedding-001")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.embed_content(
                model="models/embedding-001",
                content=text
            )
        )
        return result["embedding"]


class PerplexityProvider(LLMProvider):
    """Perplexity Sonar API provider for research tasks."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "sonar-pro"
    ):
        super().__init__(
            api_key=api_key or settings.llm.sonar_api_key,
            default_model=default_model
        )
        self.base_url = "https://api.perplexity.ai"
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Type[T]] = None,
    ) -> tuple[str, int]:
        import httpx
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model or self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
        
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        
        self.logger.debug(
            "Perplexity generation complete",
            model=model or self.default_model,
            tokens=tokens
        )
        
        return content, tokens
    
    async def generate_chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> tuple[str, int]:
        import httpx
        
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model or self.default_model,
                    "messages": formatted_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
        
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        
        return content, tokens
    
    async def embed(self, text: str) -> List[float]:
        # Perplexity doesn't have embeddings, fall back to OpenAI
        openai_provider = OpenAIProvider()
        return await openai_provider.embed(text)


# =============================================================================
# Provider Factory
# =============================================================================

PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "perplexity": PerplexityProvider,
}


@lru_cache()
def get_llm_provider(provider: Optional[str] = None) -> LLMProvider:
    """
    Get an LLM provider instance.
    
    Args:
        provider: Provider name (openai, anthropic, gemini, perplexity)
                 Defaults to settings.llm.default_provider
                 
    Returns:
        LLMProvider instance
    """
    provider_name = provider or settings.llm.default_provider
    
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return PROVIDERS[provider_name]()
