import io
import uuid
from typing import Dict, Any
from loguru import logger
from genpulse.engines.base import BaseEngine
from genpulse.clients.comfyui.client import ComfyClient
from genpulse.infra.storage import get_storage
from genpulse.handlers.registry import registry
from genpulse.types import TaskContext
from genpulse import config

@registry.register("comfyui")
class ComfyEngine(BaseEngine):
    def validate_params(self, params: Dict[str, Any]) -> bool:
        if "workflow" not in params:
            logger.error("Missing 'workflow' in params")
            return False
        return True

    async def execute(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        params = task.get("params", {})
        workflow = params["workflow"]
        # Allow override from params, but default to config
        base_url = params.get("server_address", config.COMFY_URL)
        
        client = ComfyClient(base_url=base_url)
        storage = get_storage()
        
        try:
            # 1. Queue Prompt
            await context.update_status("processing", progress=10, result={"info": "Queuing to ComfyUI"})
            prompt_id = await client.queue_prompt(workflow)
            logger.info(f"Task {task['task_id']} queued to ComfyUI as {prompt_id}")
            
            # 2. Wait for completion
            await context.update_status("processing", progress=30, result={"info": "Waiting for generation"})
            images = await client.wait_for_completion(prompt_id)
            
            # 3. Handle results
            await context.update_status("processing", progress=80, result={"info": "Uploading results"})
            urls = []
            for i, img_bytes in enumerate(images):
                # Generate a unique path for the result
                # Format: {task_id}/out_{index}_{uuid}.png
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

