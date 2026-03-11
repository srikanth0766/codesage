"""
Configuration management for the agentic AI code review system.
Handles LLM provider settings and API keys.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider Selection
    # Options: "ollama", "openai", "claude", "gemini"
    llm_provider: str = "ollama"
    
    # API Keys (optional, loaded from .env file)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    
    # Model Names
    openai_model: str = "gpt-4-turbo-preview"
    claude_model: str = "claude-3-sonnet-20240229"
    ollama_model: str = "llama3.2:3b"  # Lightweight model for local use
    gemini_model: str = "gemini-1.5-pro"
    mistral_model: str = "mistral-small-latest"
    
    # Ollama Settings
    ollama_base_url: str = "http://localhost:11434"
    
    # Analysis Options
    enable_logic_analysis: bool = True
    enable_optimizations: bool = True
    max_llm_response_time: int = 10  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
