"""
FOS Survey Agent - Configuration Module
Handles all application settings
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


# Project root directory (parent of backend folder)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "FOS Survey Agent"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database (relative to project root)
    database_path: str = str(PROJECT_ROOT / "data" / "survey_agent.db")
    
    # Dummy data (relative to project root)
    dummy_data_path: str = str(PROJECT_ROOT / "dummy_data")
    
    # AI Services
    whisper_url: str = "http://localhost:8001"
    piper_url: str = "http://localhost:8002"
    ollama_url: str = "http://localhost:11434"
    
    # LLM Settings
    llm_model: str = "llama3.1:8b"
    llm_timeout: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path"""
        path = Path(self.database_path).parent
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def dummy_data_dir(self) -> Path:
        """Get dummy data directory path"""
        return Path(self.dummy_data_path)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience access
settings = get_settings()
