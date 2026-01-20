import os
import abc
import shutil
from typing import BinaryIO, Optional
from pathlib import Path
from genpulse import config

class BaseStorage(abc.ABC):
    @abc.abstractmethod
    async def upload(self, file_path: str, content: BinaryIO, content_type: Optional[str] = None) -> str:
        """Upload file and return the URL or path string"""
        pass

    @abc.abstractmethod
    async def delete(self, file_path: str) -> bool:
        """Delete file"""
        pass

class LocalStorageProvider(BaseStorage):
    def __init__(self):
        self.base_path = Path(config.STORAGE_LOCAL_PATH).resolve()
        # Ensure the base directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.base_url = config.STORAGE_BASE_URL

    async def upload(self, file_path: str, content: BinaryIO, content_type: Optional[str] = None) -> str:
        # Resolve the full path and ensure parent directories exist
        # We use Path.joinpath to handle relative paths safely
        full_path = (self.base_path / file_path).resolve()
        
        # Security check: ensure the path is within the base path
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError(f"Path traversal attempt: {file_path}")
            
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        with open(full_path, "wb") as f:
            shutil.copyfileobj(content, f)
        
        # Construct the URL
        return f"{self.base_url}/{file_path.replace(os.sep, '/')}"

    async def delete(self, file_path: str) -> bool:
        full_path = self.base_path / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

class S3StorageProvider(BaseStorage):
    def __init__(self):
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                endpoint_url=config.S3_ENDPOINT_URL,
                aws_access_key_id=config.S3_ACCESS_KEY,
                aws_secret_access_key=config.S3_SECRET_KEY,
                region_name=config.S3_REGION_NAME
            )
        except ImportError:
            # Allow initialization to succeed but fail during upload if boto3 is missing
            self.s3 = None

    async def upload(self, file_path: str, content: BinaryIO, content_type: Optional[str] = None) -> str:
        if not self.s3:
            raise RuntimeError("boto3 is not installed or S3 client not initialized")
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
            
        # upload_fileobj is a synchronous call in boto3, 
        # for a high-concurrency app we'd normally use aiobotocore
        self.s3.upload_fileobj(
            content,
            config.S3_BUCKET_NAME,
            file_path,
            ExtraArgs=extra_args
        )
        
        if config.S3_ENDPOINT_URL:
            return f"{config.S3_ENDPOINT_URL}/{config.S3_BUCKET_NAME}/{file_path}"
        return f"https://{config.S3_BUCKET_NAME}.s3.{config.S3_REGION_NAME}.amazonaws.com/{file_path}"

    async def delete(self, file_path: str) -> bool:
        if not self.s3:
            return False
        self.s3.delete_object(Bucket=config.S3_BUCKET_NAME, Key=file_path)
        return True

_storage_instance: Optional[BaseStorage] = None

def get_storage() -> BaseStorage:
    global _storage_instance
    if _storage_instance is None:
        if config.STORAGE_TYPE == "s3":
            _storage_instance = S3StorageProvider()
        else:
            _storage_instance = LocalStorageProvider()
    return _storage_instance

