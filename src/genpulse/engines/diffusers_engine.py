import io
import uuid
from typing import Dict, Any, Optional
from loguru import logger
from genpulse.engines.base import BaseEngine
from genpulse.infra.storage import get_storage
from genpulse.features.registry import registry

# Global cache for pipelines
_PIPELINE_CACHE = {}

@registry.register("diffusers")
class DiffusersEngine(BaseEngine):
    """
    Simple Diffusers Engine for local inference.
    Supports basic text-to-image pipeline.
    """

    def validate_params(self, params: Dict[str, Any]) -> bool:
        if "prompt" not in params:
            logger.warning("Diffusers: Missing 'prompt' in parameters")
            return False
        return True

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        params = task.get("params", {})
        model_id = params.get("model_id")
        prompt = params["prompt"]
        update_status = context["update_status"]
        
        # 1. Pipeline initialization logic
        # For this "simple" version, we assume the user might provide a local path
        # If not provided and we aren't in a real environment, we'll avoid downloading.
        
        logger.info(f"Diffusers execution started Task={task['task_id']} Model={model_id}")
        await update_status("processing", progress=10, result={"info": "Initializing engine"})

        # --- MOCK LOGIC FOR SIMPLE IMPLEMENTATION ---
        # If model_id is "mock", we return a fake image to avoid downloading GBs of data
        if model_id == "mock":
            logger.debug("Running in MOCK mode to avoid downloading models")
            await update_status("processing", progress=50, result={"info": "Generating (mock)"})
            
            # Create a simple 1x1 color pixel or similar
            from PIL import Image
            img = Image.new('RGB', (512, 512), color = (73, 109, 137))
            
            storage = get_storage()
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            file_path = f"{task['task_id']}/diff_mock_{uuid.uuid4().hex[:8]}.png"
            url = await storage.upload(file_path, img_byte_arr, content_type="image/png")
            
            await update_status("processing", progress=90, result={"info": "Finalizing"})
            return {
                "images": [url],
                "model": "mock-sd",
                "provider": "diffusers"
            }
        
        # 2. Real Pipeline Logic (Implicitly disabled if model_id is not mock for now)
        # In a real scenario, you'd use:
        # from diffusers import StableDiffusionPipeline
        # pipe = StableDiffusionPipeline.from_pretrained(...)
        # For now, we raise a helpful error to avoid unintended downloads
        msg = f"Model ID '{model_id}' requires download. Run with model_id='mock' for testing."
        logger.error(msg)
        raise ValueError(msg)
