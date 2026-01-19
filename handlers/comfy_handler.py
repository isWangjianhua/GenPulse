import io
import uuid
import logging
from typing import Dict, Any
from handlers.base import BaseHandler
from core.comfy_client import ComfyClient
from core.storage import get_storage
from core.registry import registry

logger = logging.getLogger(__name__)

@registry.register("comfyui")
class ComfyUIHandler(BaseHandler):
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Expects:
        - workflow: Dict[str, Any] (The ComfyUI API nodes JSON)
        - server_address: str (Optional)
        """
        if "workflow" not in params:
            logger.error("Missing 'workflow' in params")
            return False
        return True

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        params = task.get("params", {})
        workflow = params["workflow"]
        server_address = params.get("server_address", "127.0.0.1:8188")
        update_status = context["update_status"]
        
        client = ComfyClient(server_address=server_address)
        storage = get_storage()
        
        try:
            # 1. Queue Prompt
            await update_status("processing", progress=10, result={"info": "Queuing to ComfyUI"})
            prompt_id = await client.queue_prompt(workflow)
            logger.info(f"Task {task['task_id']} queued to ComfyUI as {prompt_id}")
            
            # 2. Wait for completion
            # Simple progress update - in a real world scenarios we'd parse the WS progress
            await update_status("processing", progress=30, result={"info": "Waiting for generation"})
            images = await client.wait_for_completion(prompt_id)
            
            # 3. Handle results
            await update_status("processing", progress=80, result={"info": "Uploading results"})
            urls = []
            for i, img_bytes in enumerate(images):
                # Generate a unique path for the result
                # Format: {task_id}/result_{index}.png
                file_path = f"{task['task_id']}/out_{i}_{uuid.uuid4().hex[:8]}.png"
                url = await storage.upload(file_path, io.BytesIO(img_bytes), content_type="image/png")
                urls.append(url)
            
            return {
                "comfy_prompt_id": prompt_id,
                "images": urls,
                "count": len(urls)
            }
            
        except Exception as e:
            logger.error(f"ComfyUI execution failed: {e}")
            raise
