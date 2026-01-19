import asyncio
import logging
from typing import Any, Dict
from handlers.base import BaseHandler
from core.registry import registry

logger = logging.getLogger("ZImageHandler")

@registry.register("z-image")
class ZImageHandler(BaseHandler):
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Ensure prompt is present"""
        if "prompt" not in params:
            logger.error("Missing 'prompt' in params")
            return False
        return True

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        params = task.get("params", {})
        prompt = params.get("prompt")
        update_status = context.get("update_status")
        
        logger.info(f"Executing Z-Image generation for prompt: {prompt}")
        
        # Simulate local ComfyUI interaction with progress
        for i in range(1, 6):
            await asyncio.sleep(0.5)
            if update_status:
                await update_status("processing", progress=i*20)
        
        return {
            "url": "https://example.com/generated_image.png",
            "metadata": {"prompt_used": prompt}
        }
