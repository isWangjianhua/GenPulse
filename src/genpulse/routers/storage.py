from fastapi import APIRouter, UploadFile, File, HTTPException
from genpulse.infra.storage import get_storage
import uuid
import os
import shutil
from loguru import logger

router = APIRouter(prefix="/storage", tags=["storage"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the configured storage (Local/S3/OSS) and return its URL.
    This is the preferred way to handle large inputs (images/videos) for I2V/V2V tasks.
    """
    storage = get_storage()
    
    # Generate unique filename to prevent collisions
    # Structure: uploads/{uuid}{ext}
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        # Try to guess from content-type or default
        if file.content_type == "image/png": ext = ".png"
        elif file.content_type == "image/jpeg": ext = ".jpg"
        else: ext = ".bin"
        
    filename = f"uploads/{uuid.uuid4()}{ext}"
    
    try:
        # Upload using the storage provider
        # file.file is the file-like object
        url = await storage.upload(filename, file.file, content_type=file.content_type)
        logger.info(f"File uploaded: {filename} -> {url}")
        
        return {
            "url": url, 
            "key": filename,
            "content_type": file.content_type
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
