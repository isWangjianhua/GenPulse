import asyncio
import json
import uuid
import httpx
import websockets
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from loguru import logger

class ComfyClientError(Exception):
    """Base exception for ComfyUI client errors"""
    pass

class ComfyClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188"):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        
        # Parse host for websocket
        if "://" in self.base_url:
            self.host = self.base_url.split("://")[1]
            self.scheme = self.base_url.split("://")[0]
        else:
            self.host = self.base_url
            self.scheme = "http"
            
        self.ws_scheme = "wss" if self.scheme == "https" else "ws"

    async def check_health(self) -> bool:
        """Check if ComfyUI server is reachable"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/system_stats")
                return resp.status_code == 200
        except Exception:
            return False

    async def queue_prompt(self, prompt: Dict[str, Any]) -> str:
        """Submit a workflow prompt to ComfyUI"""
        url = f"{self.base_url}/prompt"
        payload = {"prompt": prompt, "client_id": self.client_id}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                if "prompt_id" not in data:
                     raise ComfyClientError(f"Failed to queue prompt: {data}")
                return data["prompt_id"]
        except httpx.HTTPError as e:
            raise ComfyClientError(f"HTTP Error queuing prompt: {e}")

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get history for a specific prompt_id"""
        url = f"{self.base_url}/history/{prompt_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code != 200:
                 return {}
            return response.json()

    async def get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        """Download raw image bytes from ComfyUI view API"""
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

    async def listen_progress(self, prompt_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Connect to WS and yield progress updates until completion.
        Yields dicts like: {"type": "progress", "value": 50, "max": 100} or {"type": "completed"}
        """
        ws_url = f"{self.ws_scheme}://{self.host}/ws?clientId={self.client_id}"
        
        try:
            async with websockets.connect(ws_url) as ws:
                while True:
                    try:
                        # 20 mins max idle timeout just in case
                        out = await asyncio.wait_for(ws.recv(), timeout=1200) 
                    except asyncio.TimeoutError:
                        yield {"type": "error", "message": "WebSocket Timeout"}
                        break
                        
                    if isinstance(out, str):
                        message = json.loads(out)
                        msg_type = message['type']
                        data = message['data']
                        
                        if msg_type == 'executing':
                            if data['node'] is None and data['prompt_id'] == prompt_id:
                                # Execution finished
                                yield {"type": "completed"}
                                break
                            elif data.get('prompt_id') == prompt_id:
                                # Validating specific prompt execution
                                yield {"type": "executing", "node": data.get("node")}
                                
                        elif msg_type == 'progress':
                             if data.get('prompt_id') == prompt_id:
                                 yield {
                                     "type": "progress", 
                                     "value": data.get("value"), 
                                     "max": data.get("max"),
                                     "node": data.get("node")
                                 }
                                 
                        elif msg_type == 'execution_cached':
                             if data.get('prompt_id') == prompt_id:
                                 yield {"type": "cached"}
                                 yield {"type": "completed"}
                                 break
                    else:
                        # Binary data (previews or SaveImageWebsocket)
                        # ComfyUI protocol: First 8 bytes are type/header info.
                        # Type 1 = Jpeg Preview, Type 2 = PNG (SaveImageWebsocket)
                        if len(out) > 8:
                             # We yield the raw image bytes
                             yield {"type": "binary_image", "data": out[8:]}
                        
        except Exception as e:
            logger.error(f"WS Error for {prompt_id}: {e}")
            yield {"type": "error", "message": str(e)}

    async def wait_for_images(self, prompt_id: str) -> List[bytes]:
        """
        Simplified helper: waits for completion and downloads all output images.
        Useful for simple synchronous-like usage.
        """
        async for msg in self.listen_progress(prompt_id):
            if msg["type"] == "error":
                raise ComfyClientError(msg["message"])
        
        # execution finished, fetch history
        history = await self.get_history(prompt_id)
        if prompt_id not in history:
             raise ComfyClientError(f"No history found for {prompt_id}")
             
        outputs = history[prompt_id]['outputs']
        images = []
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
