"""
Factory for creating LLM provider instances based on configuration.
"""

from .base import LLMProvider
from .ollama_provider import OllamaProvider
from config import settings


def create_llm_provider() -> LLMProvider:
    """
    Create an LLM provider based on application settings.
    
    Returns:
        Configured LLM provider instance
        
    Raises:
        ValueError: If provider is not supported or not configured
    """
    provider_name = settings.llm_provider.lower()
    
    if provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model
        )
    
    elif provider_name == "openai":
        # TODO: Implement OpenAI provider
        raise NotImplementedError("OpenAI provider not yet implemented")
    
    elif provider_name == "claude":
        # TODO: Implement Claude provider
        raise NotImplementedError("Claude provider not yet implemented")
    
    elif provider_name == "mistral":
        from .mistral_provider import MistralProvider
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY not set in environment/.env")
        return MistralProvider(
            api_key=settings.mistral_api_key,
            model=settings.mistral_model
        )

    elif provider_name == "gemini":
        from .gemini_provider import GeminiProvider
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set in environment/.env")
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")


def get_best_available_provider() -> LLMProvider:
    """
    Returns the best available LLM provider.
    Prefers Mistral → Gemini → Ollama (local).
    """
    # 1. Try Mistral
    if settings.mistral_api_key:
        try:
            from .mistral_provider import MistralProvider
            provider = MistralProvider(
                api_key=settings.mistral_api_key,
                model=settings.mistral_model
            )
            if provider.is_available():
                return provider
        except Exception:
            pass

    # 2. Try Gemini
    if settings.gemini_api_key:
        try:
            from .gemini_provider import GeminiProvider
            provider = GeminiProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model
            )
            if provider.is_available():
                return provider
        except Exception:
            pass

    # 3. Default: Ollama
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model
    )
