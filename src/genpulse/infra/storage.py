import os
import abc
import shutil
import asyncio
from typing import BinaryIO, Optional, Dict
from pathlib import Path
from genpulse import config
from loguru import logger

class BaseStorage(abc.ABC):
    @abc.abstractmethod
    async def upload(self, file_path: str, content: BinaryIO, content_type: Optional[str] = None, metadata: Dict[str, str] = None) -> str:
        """
        Upload file to storage.
        
        Args:
            file_path: Relative path/key.
            content: File-like object (binary).
            content_type: MIME type of the file.
            metadata: Custom metadata (key-value pairs) to attach to the file.
            
        Returns:
            The accessible URL (signed if S3, public if local).
        """
        pass

    @abc.abstractmethod
    async def delete(self, file_path: str) -> bool:
        """Delete file from storage."""
        pass
        
    @abc.abstractmethod
    async def get_url(self, file_path: str) -> str:
        """Get access URL (e.g., presigned or public)."""
        pass

class LocalStorageProvider(BaseStorage):
    def __init__(self):
        self.base_path = Path(config.STORAGE_LOCAL_PATH).resolve()
        # Ensure the base directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.base_url = config.STORAGE_BASE_URL

    async def upload(self, file_path: str, content: BinaryIO, content_type: Optional[str] = None, metadata: Dict[str, str] = None) -> str:
        # Resolve the full path and ensure parent directories exist
        full_path = (self.base_path / file_path).resolve()
        
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError(f"Path traversal attempt: {file_path}")
            
        # Offload blocking I/O to thread
        await asyncio.to_thread(self._write_file, full_path, content)
        
        # Local storage doesn't support metadata in the same way, we rely on DB.
        # But we return the URL.
        return await self.get_url(file_path)
        
    def _write_file(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure pointer is at start if it was read before
        if content.seekable():
             content.seek(0)
        with open(path, "wb") as f:
            shutil.copyfileobj(content, f)

    async def delete(self, file_path: str) -> bool:
        full_path = self.base_path / file_path
        if full_path.exists():
            await asyncio.to_thread(full_path.unlink)
            return True
        return False
        
    async def get_url(self, file_path: str) -> str:
        # Simple static file mapping
        return f"{self.base_url}/{file_path.replace(os.sep, '/')}"

class S3StorageProvider(BaseStorage):
    def __init__(self):
        try:
            import boto3
        except ImportError:
            raise RuntimeError("boto3 is not installed. Please install it to use S3StorageProvider.")
            
        self.bucket = config.S3_BUCKET_NAME
        
        # Initialize boto3 client (synchronous, but we run calls in threads)
        self.s3_client = boto3.client(
            's3',
            endpoint_url=config.S3_ENDPOINT_URL,
            aws_access_key_id=config.S3_ACCESS_KEY,
            aws_secret_access_key=config.S3_SECRET_KEY,
            region_name=config.S3_REGION_NAME
        )
        logger.info(f"Initialized S3 Storage (Bucket: {self.bucket})")

    async def upload(self, file_path: str, content: BinaryIO, content_type: Optional[str] = None, metadata: Dict[str, str] = None) -> str:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        if metadata:
            # S3 Metadata must be strings
            extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}

        if content.seekable():
             content.seek(0)

        await asyncio.to_thread(
            self.s3_client.upload_fileobj,
            content,
            self.bucket,
            file_path,
            ExtraArgs=extra_args
        )
        logger.info(f"Uploaded {file_path} to S3")
        return await self.get_url(file_path)

    async def delete(self, file_path: str) -> bool:
        try:
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=self.bucket,
                Key=file_path
            )
            return True
        except Exception as e:
            logger.error(f"S3 Delete Error: {e}")
            return False

    async def get_url(self, file_path: str) -> str:
        # Generate presigned URL valid for 1 hour (3600 seconds)
        try:
            url = await asyncio.to_thread(
                self.s3_client.generate_presigned_url,
                'get_object',
                Params={'Bucket': self.bucket, 'Key': file_path},
                ExpiresIn=3600
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return ""

_storage_instance: Optional[BaseStorage] = None

def get_storage() -> BaseStorage:
    global _storage_instance
    if _storage_instance is None:
        # Both S3 and Aliyun OSS use the S3 Protocol via boto3
        # For OSS, ensure S3_ENDPOINT_URL is set to something like "https://oss-cn-hangzhou.aliyuncs.com"
        if config.STORAGE_TYPE in ["s3", "oss"]:
            _storage_instance = S3StorageProvider()
        else:
            _storage_instance = LocalStorageProvider()
    return _storage_instance
