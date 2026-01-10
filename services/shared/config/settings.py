# =============================================================================
# Shared Configuration Settings
# =============================================================================
# Centralized configuration management using Pydantic Settings
# =============================================================================

from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    
    model_config = SettingsConfigDict(env_prefix="DATABASE_")
    
    url: str = Field(
        default="postgresql://localhost:5432/investment_system",
        description="PostgreSQL connection URL"
    )
    pool_size: int = Field(default=5, ge=1, le=20)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=5, le=120)
    echo: bool = Field(default=False, description="Echo SQL statements")


class RedisSettings(BaseSettings):
    """Redis connection settings."""
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")
    
    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    max_connections: int = Field(default=10, ge=1, le=100)
    decode_responses: bool = Field(default=True)
    channel_prefix: str = Field(default="investment-agents")


class LLMSettings(BaseSettings):
    """LLM provider settings."""
    
    model_config = SettingsConfigDict(env_prefix="")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(default=None, alias="OPENAI_API_BASE")
    openai_default_model: str = Field(default="gpt-4-turbo-preview")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_default_model: str = Field(default="claude-3-sonnet-20240229")
    
    # Google Gemini
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_default_model: str = Field(default="gemini-2.5-flash")
    
    # Perplexity (for research)
    sonar_api_key: Optional[str] = Field(default=None, alias="SONAR_API_KEY")
    
    # Default provider
    default_provider: str = Field(default="openai")
    fallback_provider: str = Field(default="anthropic")
    
    # Rate limiting
    max_tokens_per_minute: int = Field(default=100000)
    max_requests_per_minute: int = Field(default=60)


class VectorDBSettings(BaseSettings):
    """Vector database settings for knowledge storage."""
    
    model_config = SettingsConfigDict(env_prefix="PINECONE_")
    
    api_key: Optional[str] = Field(default=None)
    environment: str = Field(default="us-east-1")
    index_name: str = Field(default="investment-knowledge")
    dimension: int = Field(default=1536)  # OpenAI ada-002 embedding dimension
    metric: str = Field(default="cosine")


class FinancialDataSettings(BaseSettings):
    """Financial data API settings."""
    
    model_config = SettingsConfigDict(env_prefix="")
    
    # Polygon.io
    polygon_api_key: Optional[str] = Field(default=None, alias="POLYGON_API_KEY")
    
    # Financial Modeling Prep
    fmp_api_key: Optional[str] = Field(default=None, alias="FMP_API_KEY")
    
    # FRED (Federal Reserve Economic Data)
    fred_api_key: Optional[str] = Field(default=None, alias="FRED_API_KEY")
    
    # Trading Economics
    trading_economics_key: Optional[str] = Field(default=None, alias="TRADING_ECONOMICS_KEY")


class StorageSettings(BaseSettings):
    """Object storage settings (S3-compatible)."""
    
    model_config = SettingsConfigDict(env_prefix="SPACES_")
    
    access_key: Optional[str] = Field(default=None)
    secret_key: Optional[str] = Field(default=None)
    bucket: str = Field(default="investment-agent-storage")
    region: str = Field(default="nyc3")
    endpoint: str = Field(default="https://nyc3.digitaloceanspaces.com")


class AuthSettings(BaseSettings):
    """Authentication settings."""
    
    model_config = SettingsConfigDict(env_prefix="")
    
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")


class AgentSettings(BaseSettings):
    """Agent-specific settings."""
    
    model_config = SettingsConfigDict(env_prefix="AGENT_")
    
    task_timeout_seconds: int = Field(default=300, ge=30, le=3600)
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay_seconds: int = Field(default=5, ge=1, le=60)
    max_concurrent_tasks: int = Field(default=10, ge=1, le=100)
    
    # Prompt settings
    prompts_directory: str = Field(default="/app/prompts")
    
    # Knowledge base settings
    knowledge_search_top_k: int = Field(default=5, ge=1, le=20)
    knowledge_similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class Settings(BaseSettings):
    """Main application settings aggregating all sub-settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application metadata
    app_name: str = Field(default="Investment Agent System")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Sub-settings (loaded separately)
    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings()
    
    @property
    def redis(self) -> RedisSettings:
        return RedisSettings()
    
    @property
    def llm(self) -> LLMSettings:
        return LLMSettings()
    
    @property
    def vector_db(self) -> VectorDBSettings:
        return VectorDBSettings()
    
    @property
    def financial_data(self) -> FinancialDataSettings:
        return FinancialDataSettings()
    
    @property
    def storage(self) -> StorageSettings:
        return StorageSettings()
    
    @property
    def auth(self) -> AuthSettings:
        return AuthSettings()
    
    @property
    def agent(self) -> AgentSettings:
        return AgentSettings()
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience function for direct import
settings = get_settings()
