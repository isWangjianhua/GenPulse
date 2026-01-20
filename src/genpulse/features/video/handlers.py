import logging
import asyncio
from typing import Dict, Any
from genpulse.features.base import BaseHandler
from genpulse.features.registry import registry
from genpulse import config

logger = logging.getLogger("VideoHandler")

def get_volc_client():
    try:
        from genpulse.clients.volcengine.client import VolcEngineClient
        return VolcEngineClient()
    except ImportError:
        raise ImportError("VolcEngine SDK not installed.")

@registry.register("text-to-video")
class TextToVideoHandler(BaseHandler):
    def validate_params(self, params: Dict[str, Any]) -> bool:
        # Relaxed validation to support multiple providers
        return True

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        params = task.get("params", {})
        provider = params.get("provider", config.DEFAULT_VIDEO_PROVIDER).lower()
        update_status = context.get("update_status")
        
        logger.info(f"Executing Text-to-Video via {provider}")
        
        if provider == "volcengine":
            client = get_volc_client()
            
            # Define callback to bridge Client progress to Worker progress
            async def callback(resp):
                if update_status:
                    # Map 'running' to 'processing'
                    # You could also add percentage logic if the API supported it
                    await update_status("processing", result={"api_status": resp.status})

            # VolcEngine requires 'content' list for T2V, but maybe user sent 'prompt'
            # Let's do a simple adapter if needed
            if "content" not in params and "prompt" in params:
                 # Auto-adapt simple prompt to Volc structure
                 params["content"] = [{"type": "text", "text": params["prompt"]}]
            
            try:
                # We reuse the client's high-level generate method which handles polling
                response = await client.generate_video(
                    params,
                    wait=True,
                    callback=callback
                )
                
                if response.status != "succeeded":
                    raise Exception(f"Video generation failed: {response.status}")
                    
                return {"status": "succeeded", "data": response.model_dump(), "provider": "volcengine"}
            except Exception as e:
                logger.error(f"VolcEngine T2V failed: {e}")
                raise e

        else:
            raise ValueError(f"Provider '{provider}' not supported for text-to-video")


@registry.register("image-to-video")
class ImageToVideoHandler(BaseHandler):
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return True

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        params = task.get("params", {})
        provider = params.get("provider", config.DEFAULT_VIDEO_PROVIDER).lower()
        update_status = context.get("update_status")
        
        if provider == "volcengine":
            client = get_volc_client()
            async def callback(resp):
                if update_status:
                    await update_status("processing", result={"api_status": resp.status})
            
            # Simple Adapter for I2V
            # If user provided 'image_url' but Volc needs 'content' list
            if "content" not in params and "image_url" in params:
                content = [{"type": "image_url", "image_url": params["image_url"]}]
                if "prompt" in params:
                    content.append({"type": "text", "text": params["prompt"]})
                params["content"] = content

            try:
                response = await client.generate_video(params, wait=True, callback=callback)
                if response.status != "succeeded":
                    raise Exception(f"Video generation failed: {response.status}")
                return {"status": "succeeded", "data": response.model_dump(), "provider": "volcengine"}
            except Exception as e:
                logger.error(f"VolcEngine I2V failed: {e}")
                raise e

        else:
             raise ValueError(f"Provider '{provider}' not supported for image-to-video")
             
@registry.register("video-to-video")
class VideoToVideoHandler(BaseHandler):
    # Placeholder for future expansion
     def validate_params(self, params: Dict[str, Any]) -> bool:
        return True
     async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
         raise NotImplementedError("Video-to-Video not yet configured")

