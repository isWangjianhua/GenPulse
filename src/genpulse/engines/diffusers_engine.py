import io
import uuid
import asyncio
from typing import Dict, Any, Optional
from loguru import logger
from genpulse.engines.base import BaseEngine
from genpulse.infra.storage import get_storage
from genpulse.handlers.registry import registry
from genpulse.types import TaskContext, EngineError

# Global cache for pipelines to avoid repeated loading
_PIPELINE_CACHE: Dict[str, Any] = {}

@registry.register("diffusers")
class DiffusersEngine(BaseEngine):
    """
    Standardized Diffusers Engine.
    Provides a mock mode for testing and a structured path for real pipeline execution.
    """

    def validate_params(self, params: Dict[str, Any]) -> bool:
        if "prompt" not in params:
            logger.warning("Diffusers: Missing 'prompt' in parameters")
            return False
        return True

    async def execute(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        params = task.get("params", {})
        model_id = params.get("model_id", "mock").lower()
        prompt = params["prompt"]
        
        logger.info(f"Diffusers execution started Task={context.task_id} Model={model_id}")
        await context.set_processing(progress=10, info="Initializing engine")

        try:
            if model_id == "mock":
                return await self._execute_mock(task, context)
            
            # Placeholder for real inference
            return await self._execute_real(task, context, model_id, prompt, params)

        except Exception as e:
            logger.error(f"Diffusers engine failed: {e}")
            raise EngineError(f"Diffusers execution error: {str(e)}", provider="diffusers")

    async def _execute_mock(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        """Fast mock execution path for development"""
        logger.debug("Running in MOCK mode")
        await context.set_processing(progress=50, info="Generating (mock)")
        
        # Simulate some async work
        await asyncio.sleep(0.5)

        from PIL import Image
        img = Image.new('RGB', (512, 512), color=(73, 109, 137))
        
        storage = get_storage()
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        file_path = f"{context.task_id}/diff_mock_{uuid.uuid4().hex[:8]}.png"
        url = await storage.upload(file_path, img_byte_arr, content_type="image/png")
        
        await context.set_processing(progress=90, info="Finalizing")
        return {
            "images": [url],
            "model": "mock-sd",
            "provider": "diffusers"
        }

    async def _execute_real(self, task: Dict[str, Any], context: TaskContext, model_id: str, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Real inference path (currently blocked to avoid downloads)"""
        # In the future, this will import diffusers and run stable diffusion
        msg = f"Model ID '{model_id}' requires download. Run with model_id='mock' for local testing."
        raise EngineError(msg, provider="diffusers")

    async def _get_pipeline(self, model_id: str):
        """Helper to load and cache pipelines"""
        if model_id in _PIPELINE_CACHE:
            return _PIPELINE_CACHE[model_id]
        
        # import diffusers ...
        # pipe = StableDiffusionPipeline.from_pretrained(model_id)
        # _PIPELINE_CACHE[model_id] = pipe
        # return pipe
        raise NotImplementedError("Real pipeline loading not enabled yet")
