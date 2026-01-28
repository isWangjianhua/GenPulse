import base64
import re
import io
import uuid
import asyncio
from typing import Dict, Any, Union, List
from genpulse.infra.storage import get_storage
from loguru import logger

# Regex to capture Data URI scheme: data:image/png;base64,.....
BASE64_PATTERN = re.compile(r"^data:(image|video|audio)/([a-zA-Z0-9]+);base64,(.+)$")

async def process_base64_inputs(data: Union[Dict, List, Any]) -> Any:
    """
    Recursively scans data (dict or list) for Base64 Data URI strings.
    Uploads them to storage and replaces the string with the resulting URL.
    """
    storage = get_storage()
    
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_dict[key] = await process_base64_inputs(value)
        return new_dict
        
    elif isinstance(data, list):
        return [await process_base64_inputs(item) for item in data]
        
    elif isinstance(data, str):
        # Check if string is a Data URI
        match = BASE64_PATTERN.match(data) # match() checks from beginning
        
        # Optimization: only check if starts with 'data:'
        if data.startswith("data:") and match:
            mime_type = f"{match.group(1)}/{match.group(2)}"
            ext = match.group(2)
            # Fix common extension mapping if needed (e.g. jpeg -> jpg)
            if ext == "jpeg": ext = "jpg"
            
            b64_str = match.group(3)
            
            try:
                logger.info("Detected Base64 input. Uploading to storage...")
                
                # Decode in thread to avoid blocking loop for large images
                binary_data = await asyncio.to_thread(base64.b64decode, b64_str)
                
                filename = f"uploads/b64_{uuid.uuid4()}.{ext}"
                
                url = await storage.upload(filename, io.BytesIO(binary_data), content_type=mime_type)
                return url
                
            except Exception as e:
                logger.error(f"Failed to upload base64 content: {e}")
                # Return original string if failure? Or raise?
                # Best to let it pass and fail downstream validation (not a valid URL)
                return data
                
    return data
