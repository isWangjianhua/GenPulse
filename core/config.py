import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Overall Environment
    ENV: str = "dev"  # dev, test, main
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    TASK_QUEUE_NAME: str = "tasks:pending"
    
    # Database Configuration
    DATABASE_URL: Optional[str] = "postgresql+asyncpg://postgres:postgres@localhost:5432/genpulse"
    
    # Storage Configuration
    STORAGE_TYPE: str = "local"  # local, s3
    STORAGE_LOCAL_PATH: str = "data/assets"
    STORAGE_BASE_URL: str = "http://localhost:8000/assets"
    
    # S3 Configuration
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = "genpulse"
    S3_REGION_NAME: Optional[str] = "us-east-1"

    # Local Libs Configuration
    AUTO_START_LOCAL_LIBS: bool = True
    
    # ComfyUI Configuration
    COMFY_ENABLE_LOCAL: bool = True
    COMFY_CPU_ONLY: bool = True
    COMFY_PORT: int = 8188
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = 'utf-8',
        extra = 'ignore'
    )

    @property
    def redis_prefix(self) -> str:
        prefixes = {
            "dev": "dev:",
            "test": "test:",
            "main": "prod:"
        }
        return prefixes.get(self.ENV, "dev:")

settings = Settings()
