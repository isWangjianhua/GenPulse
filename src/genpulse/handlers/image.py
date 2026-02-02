from loguru import logger
import asyncio
from typing import Dict, Any, Optional
from genpulse.handlers.base import BaseHandler
from genpulse.handlers.registry import registry
from genpulse import config
from genpulse.types import TaskContext

# --- Helpers / Lazy Imports ---

def get_volc_client():
    from genpulse.clients.volcengine.client import create_volcengine_client
    return create_volcengine_client()

def get_tencent_client():
    from genpulse.clients.tencent.client import create_tencent_vod_client
    return create_tencent_vod_client()

def get_baidu_client():
    from genpulse.clients.baidu.client import create_baidu_vod_client
    return create_baidu_vod_client()

def get_minimax_client():
    from genpulse.clients.minimax.client import create_minimax_client
    return create_minimax_client()

def get_dashscope_client():
    from genpulse.clients.dashscope.client import create_dashscope_client
    return create_dashscope_client()

def get_kling_client():
    from genpulse.clients.kling.client import create_kling_client
    return create_kling_client()


# --- Text to Image ---

@registry.register("text-to-image")
class TextToImageHandler(BaseHandler):
    """
    Unified Handler for Text-to-Image Generation.
    Supports: VolcEngine, Tencent, Baidu, DashScope, MiniMax, Kling, ComfyUI, Diffusers.
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
        
        try:
            # --- VolcEngine ---
            if provider == "volcengine":
                client = get_volc_client()
                response = await client.generate_image(params)
                if response.error:
                    raise Exception(response.error.message)
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- Tencent ---
            elif provider == "tencent":
                from genpulse.clients.tencent.schemas import TencentImageParams
                client = get_tencent_client()
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
                response = await client.generate_image(tencent_params, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"Tencent T2I failed: {response.message}")
                return {"status": "succeeded", "result_url": response.result_url, "data": response.model_dump(), "provider": provider}

            # --- Baidu ---
            elif provider == "baidu":
                # Uses generic params adapter
                client = get_baidu_client()
                # Baidu expects: model, taskInput={text}
                # Adapter:
                bp = {
                    "model": params.get("model", "Stable-Diffusion-XL"),
                    "taskInput": {"text": params.get("prompt")}
                }
                # Add optional params
                if "negative_prompt" in params:
                    bp["taskInput"]["negative_text"] = params["negative_prompt"]
                if "resolution" in params:
                    bp["taskInput"]["resolution"] = params["resolution"]
                if "style" in params:
                    bp["taskInput"]["style"] = params["style"]

                response = await client.text_to_image(bp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"Baidu T2I failed: {response.result or response.status}")
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- DashScope ---
            elif provider == "dashscope":
                client = get_dashscope_client()
                # Adapter:
                dp = {
                    "model": params.get("model", "wanx-v1"),
                    "prompt": params.get("prompt")
                }
                if "n" in params: dp["n"] = params["n"]
                if "size" in params: dp["size"] = params["size"]
                if "style" in params: dp["style"] = params["style"]

                response = await client.generate_image(dp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"DashScope T2I failed: {response.message}")
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- MiniMax ---
            elif provider == "minimax":
                client = get_minimax_client()
                # Adapter
                mp = {
                    "model": params.get("model", "image-01"),
                    "prompt": params.get("prompt")
                }
                if "aspect_ratio" in params: mp["aspect_ratio"] = params["aspect_ratio"]

                response = await client.generate_image(mp)
                if not response.is_succeeded:
                    raise Exception(f"MiniMax T2I failed")
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- ComfyUI ---
            elif provider == "comfyui":
                from genpulse.engines.comfy_engine import ComfyEngine
                
                # Map generic T2I params to Comfy Template
                # We default to 'sdxl_t2i' template. 
                # If user wants a specific template, they should use 'comfyui' engine directly in task type?
                # Actually, ImageHandler acts as facade.
                
                template = params.get("model", "sdxl_t2i")
                if template == "sdxl": template = "sdxl_t2i" # alias
                
                template_inputs = {
                    "prompt": params.get("prompt"),
                    "negative_prompt": params.get("negative_prompt"),
                    "width": params.get("width"),
                    "height": params.get("height"),
                    "seed": params.get("seed"),
                    "steps": params.get("steps")
                }
                # Remove empty inputs so defaults apply
                template_inputs = {k: v for k, v in template_inputs.items() if v is not None}

                new_task = {
                    "task_id": task.get("task_id"),
                    "params": {
                        "template_name": template,
                        "inputs": template_inputs,
                        "server_address": params.get("server_address")
                    }
                }
                
                logger.info(f"Delegating to ComfyEngine with template: {template}")
                handler = ComfyEngine()
                return await handler.execute(new_task, context)

            # --- Diffusers ---
            elif provider == "diffusers":
                from genpulse.engines.diffusers_engine import DiffusersEngine
                handler = DiffusersEngine()
                return await handler.execute(task, context)

            else:
                raise ValueError(f"Unknown provider '{provider}' for text-to-image")

        except Exception as e:
            logger.error(f"{provider} T2I failed: {e}")
            raise e


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

        try:
            # --- VolcEngine ---
            if provider == "volcengine":
                client = get_volc_client()
                response = await client.generate_image(params)
                if response.error:
                     raise Exception(response.error.message)
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- Baidu ---
            elif provider == "baidu":
                client = get_baidu_client()
                bp = {
                    "model": params.get("model", "Stable-Diffusion-XL"),
                    "taskInput": {
                        "text": params.get("prompt", ""),
                        "image": params.get("image_url") or params.get("image")
                    }
                }
                response = await client.image_to_image(bp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"Baidu I2I failed")
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- DashScope ---
            elif provider == "dashscope":
                # DashScope supports Image Repaint/Edit via different endpoints usually
                # Here we map basic I2I if available or Image Edit
                client = get_dashscope_client()
                # Assuming using qwen-vl or specialized model for edit
                # For standard I2I (Generation), DashScope uses "sketch_to_image_synthesis" or similar
                # Let's map to 'edit_image' if model suggests it, or try generate
                if "edit" in params.get("model", ""):
                     ep = {
                         "model": params.get("model"),
                         "input": {"image_path": params.get("image_url")},
                         "parameters": {"prompt": params.get("prompt")}
                     }
                     response = await client.edit_image(ep)
                else:
                    # Fallback or generic I2I implementation if available
                    # For now DashScope Python SDK mainly exposes T2I and Repaint
                     raise NotImplementedError("DashScope standard I2I not fully mapped yet")
                
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}
            
            else:
                raise ValueError(f"Provider '{provider}' not supported for image-to-image yet")

        except Exception as e:
            logger.error(f"{provider} I2I failed: {e}")
            raise e

