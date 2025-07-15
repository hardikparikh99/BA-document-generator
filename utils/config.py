"""
Configuration management for the CrewAI Multi-Agent Project Documentation System.
This module handles loading environment variables and providing configuration settings.
"""
import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Primary Configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        env="OPENAI_MODEL"
    )
    
    # Ollama Fallback Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(
        default="llama3.2:1b",
        env="OLLAMA_MODEL"
    )
    
    # Pinecone Configuration
    pinecone_api_key: Optional[str] = Field(
        default=None,
        env="PINECONE_API_KEY"
    )
    pinecone_environment: Optional[str] = Field(
        default=None,
        env="PINECONE_ENVIRONMENT"
    )
    pinecone_index_name: str = Field(
        default="transcription-index",
        env="PINECONE_INDEX_NAME"
    )
    
    # File Upload Settings
    max_file_size: str = Field(
        default="500MB",
        env="MAX_FILE_SIZE"
    )
    temp_file_retention: int = Field(
        default=24
        # Direct environment variable access to avoid parsing issues
    )
    
    # Application Settings
    debug: bool = Field(
        default=True,
        env="DEBUG"
    )
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    
    # Derived settings
    max_file_size_bytes: int = 0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **data):
        super().__init__(**data)
        # Convert max_file_size to bytes
        size_str = self.max_file_size.upper()
        if size_str.endswith('KB'):
            self.max_file_size_bytes = int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            self.max_file_size_bytes = int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            self.max_file_size_bytes = int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            try:
                self.max_file_size_bytes = int(size_str)
            except ValueError:
                self.max_file_size_bytes = 500 * 1024 * 1024  # Default to 500MB

# Clear cache and reload environment variables
def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings: Application settings
    """
    # Reload environment variables
    load_dotenv(override=True)
    return Settings()

def get_temp_dir() -> str:
    """
    Get the temporary directory path for file storage.
    
    Returns:
        str: Path to temporary directory
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(base_dir, "temp_files")
    
    # Create directory if it doesn't exist
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    return temp_dir
