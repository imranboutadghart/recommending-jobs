"""Configuration management using Pydantic Settings"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Google Gemini API
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/jobs.db",
        description="Database connection URL"
    )
    
    # Job API Keys (Optional)
    adzuna_app_id: Optional[str] = Field(default=None, description="Adzuna App ID")
    adzuna_api_key: Optional[str] = Field(default=None, description="Adzuna API Key")
    jooble_api_key: Optional[str] = Field(default=None, description="Jooble API Key")
    
    # Application Settings
    app_host: str = Field(default="0.0.0.0", description="Application host")
    app_port: int = Field(default=8000, description="Application port")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Embedding Settings
    doc2vec_model_path: str = Field(
        default="./data/doc2vec.model",
        description="Path to saved Doc2Vec model"
    )
    doc2vec_vector_size: int = Field(
        default=100,
        description="Size of the embedding vectors"
    )
    max_embedding_batch_size: int = Field(
        default=100,
        description="Maximum number of texts to embed in one batch"
    )
    
    # Job Search Settings
    max_jobs_per_source: int = Field(
        default=50,
        description="Maximum jobs to fetch from each source"
    )
    default_location: str = Field(
        default="United States",
        description="Default job search location"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
