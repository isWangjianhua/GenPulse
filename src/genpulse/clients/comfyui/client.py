import asyncio
import json
import uuid
import httpx
import websockets
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ComfyClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188"):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        
        # Parse host for websocket
        # Simplistic parsing, robust code would use urllib.parse
        if "://" in self.base_url:
            self.host = self.base_url.split("://")[1]
        else:
            self.host = self.base_url

    async def queue_prompt(self, prompt: Dict[str, Any]) -> str:
        url = f"{self.base_url}/prompt"
        payload = {"prompt": prompt, "client_id": self.client_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["prompt_id"]

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/history/{prompt_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        url = f"{self.base_url}/view"
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.content

    async def wait_for_completion(self, prompt_id: str) -> List[bytes]:
        """
        Connect to WS and wait for the specific prompt_id execution to finish.
        Returns a list of image bytes.
        """
        ws_url = f"ws://{self.host}/ws?clientId={self.client_id}"
        images = []
        
        try:
            async with websockets.connect(ws_url) as ws:
                while True:
                    out = await ws.recv()
                    if isinstance(out, str):
                        message = json.loads(out)
                        if message['type'] == 'executing':
                            data = message['data']
                            if data['node'] is None and data['prompt_id'] == prompt_id:
                                # Execution finished
                                break
                    else:
                        # Binary data (previews) - ignored for now
                        continue
            
            # After breaking, get history to find output filenames
            history = await self.get_history(prompt_id)
            outputs = history[prompt_id]['outputs']
            for node_id in outputs:
                node_output = outputs[node_id]
                if 'images' in node_output:
                    for image in node_output['images']:
                        img_bytes = await self.get_image(
                            image['filename'], 
                            image['subfolder'], 
                            image['type']
                        )
                        images.append(img_bytes)
            
            return images
        except Exception as e:
            logger.error(f"Error waiting for ComfyUI task {prompt_id}: {e}")
            raise

