from loguru import logger
import asyncio
from typing import Dict, Any, Optional
from genpulse.handlers.base import BaseHandler
from genpulse.handlers.registry import registry
from genpulse import config
from genpulse.types import TaskContext

# --- Helpers / Lazy Imports ---
# We keep these separate to avoid dependency hell if a user doesn't use a specific provider

def get_volc_client():
    try:
        from genpulse.clients.volcengine.client import VolcEngineClient
        return VolcEngineClient()
    except ImportError:
        raise ImportError("VolcEngine SDK not installed.")

def get_tencent_client():
    try:
        from genpulse.clients.tencent.client import create_tencent_vod_client
        return create_tencent_vod_client()
    except ImportError:
        raise ImportError("Tencent Cloud SDK not installed.")


# --- Text to Image ---

@registry.register("text-to-image")
class TextToImageHandler(BaseHandler):
    """
    Unified Handler for Text-to-Image Generation.
    Supports: VolcEngine, ComfyUI, Diffusers.
    """
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        if "prompt" not in params:
            logger.error("Missing 'prompt' in params")
            return False
        return True

    async def execute(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        params = task.get("params", {})
        provider = params.get("provider", config.DEFAULT_IMAGE_PROVIDER).lower()
        
        logger.info(f"Executing Text-to-Image via {provider}")
        
        # --- VolcEngine ---
        if provider == "volcengine":
            client = get_volc_client()
            # Volcengine params: model, prompt
            # We explicitly map or passthrough
            try:
                response = await client.generate_image(params)
                if response.error:
                    raise Exception(response.error.message)
                return {"status": "succeeded", "data": response.model_dump(), "provider": "volcengine"}
            except Exception as e:
                logger.error(f"VolcEngine T2I failed: {e}")
                raise e

        # --- ComfyUI ---
        elif provider == "comfyui":
            # We can import the existing logic or helper
            # To keep it "flat", we treat the old handler as a library
            from genpulse.engines.comfy_engine import ComfyEngine
            # We use the handler logic but manually, or we can instantiate it
            # note: ComfyEngine usually expects 'workflow' in params
            handler = ComfyEngine()
            return await handler.execute(task, context)

        # --- Diffusers (Local) ---
        elif provider == "diffusers":
            from genpulse.engines.diffusers_engine import DiffusersEngine
            handler = DiffusersEngine()
            return await handler.execute(task, context)

        # --- Tencent VOD (Cloud) ---
        elif provider == "tencent":
            from genpulse.clients.tencent.schemas import TencentImageParams
            client = get_tencent_client()
            
            # Map standard params to Tencent specifics
            # Tencent expects: ModelName, ModelVersion, Prompt, NegativePrompt, OutputConfig
            tencent_params = TencentImageParams(
                ModelName=params.get("model_name", "Hunyuan"),
                ModelVersion=params.get("model_version", "3.0"),
                Prompt=params.get("prompt"),
                NegativePrompt=params.get("negative_prompt"),
                OutputConfig={
                    "AspectRatio": params.get("aspect_ratio", "16:9"),
                    "Resolution": params.get("resolution", "1024x576")
                }
            )
            
            try:
                response = await client.generate_image(tencent_params, wait=True)
                if not response.is_succeeded:
                    error_msg = response.AigcImageTask.Message if response.AigcImageTask else "Unknown Tencent error"
                    raise Exception(f"Tencent T2I failed: {error_msg}")
                    
                return {
                    "status": "succeeded",
                    "result_url": response.result_url,
                    "data": response.model_dump(),
                    "provider": "tencent"
                }
            except Exception as e:
                logger.error(f"Tencent T2I failed: {e}")
                raise e

        else:
            raise ValueError(f"Unknown provider '{provider}' for text-to-image")


# --- Image to Image ---

@registry.register("image-to-image")
class ImageToImageHandler(BaseHandler):
    """
    Unified Handler for Image-to-Image Generation.
    """
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return ("image" in params or "image_url" in params)

    async def execute(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        params = task.get("params", {})
        provider = params.get("provider", config.DEFAULT_IMAGE_PROVIDER).lower()
        
        logger.info(f"Executing Image-to-Image via {provider}")

        if provider == "volcengine":
            # Note: VolcEngine I2I uses generate_image but with 'image' param
            client = get_volc_client()
            try:
                response = await client.generate_image(params)
                if response.error:
                     raise Exception(response.error.message)
                return {"status": "succeeded", "data": response.model_dump(), "provider": "volcengine"}
            except Exception as e:
                logger.error(f"VolcEngine I2I failed: {e}")
                raise e
                
        # Add other providers (ComfyUI I2I) here
        
        else:
            raise ValueError(f"Provider '{provider}' not supported for image-to-image yet")

