from loguru import logger
import asyncio
from typing import Dict, Any
from genpulse.handlers.base import BaseHandler
from genpulse.handlers.registry import registry
from genpulse import config
from genpulse.types import TaskContext

# --- Helpers ---

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


@registry.register("text-to-video")
class TextToVideoHandler(BaseHandler):
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return True

    async def execute(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        params = task.get("params", {})
        provider = params.get("provider", config.DEFAULT_VIDEO_PROVIDER).lower()
        
        logger.info(f"Executing Text-to-Video via {provider}")
        
        try:
            # --- VolcEngine ---
            if provider == "volcengine":
                client = get_volc_client()
                async def callback(resp):
                    await context.update_status("processing", result={"api_status": resp.status})

                if "content" not in params and "prompt" in params:
                     params["content"] = [{"type": "text", "text": params["prompt"]}]
                
                response = await client.generate_video(params, wait=True, callback=callback)
                if response.status != "succeeded":
                    raise Exception(f"Video generation failed: {response.status}")
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- Tencent ---
            elif provider == "tencent":
                from genpulse.clients.tencent.schemas import TencentVideoParams
                client = get_tencent_client()
                tencent_params = TencentVideoParams(
                    ModelName=params.get("model_name", "Hunyuan"),
                    ModelVersion=params.get("model_version", "1.5"),
                    Prompt=params.get("prompt"),
                    NegativePrompt=params.get("negative_prompt"),
                    OutputConfig={
                        "AspectRatio": params.get("aspect_ratio", "16:9"),
                        "Resolution": params.get("resolution", "720P")
                    }
                )
                response = await client.generate_video(tencent_params, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"Tencent T2V failed: {response.AigcVideoTask.Message}")
                return {"status": "succeeded", "result_url": response.result_url, "data": response.model_dump(), "provider": provider}

            # --- Baidu ---
            elif provider == "baidu":
                client = get_baidu_client()
                # Adapter
                bp = {
                    "model": params.get("model", "univid-v2"),
                    "taskInput": {"text": params.get("prompt")}
                }
                response = await client.text_to_video(bp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"Baidu T2V failed: {response.result or response.status}")
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- MiniMax ---
            elif provider == "minimax":
                client = get_minimax_client()
                mp = {
                    "model": params.get("model", "video-01"),
                    "prompt": params.get("prompt")
                }
                response = await client.generate_video(mp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"MiniMax T2V failed: {response.base_resp.status_msg}")
                return {"status": "succeeded", "result_url": response.download_url, "data": response.model_dump(), "provider": provider}

            # --- Kling ---
            elif provider == "kling":
                client = get_kling_client()
                kp = {
                    "model": params.get("model", "kling-v1"),
                    "prompt": params.get("prompt")
                }
                if "negative_prompt" in params: kp["negative_prompt"] = params["negative_prompt"]
                if "aspect_ratio" in params: kp["aspect_ratio"] = params["aspect_ratio"]
                if "duration" in params: kp["duration"] = str(params["duration"])

                response = await client.text_to_video(kp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"Kling T2V failed: {response.message}")
                # Kling returns specific data structure
                video_url = response.data.task_result.videos[0].url if response.data.task_result and response.data.task_result.videos else None
                return {"status": "succeeded", "result_url": video_url, "data": response.model_dump(), "provider": provider}

            # --- DashScope ---
            elif provider == "dashscope":
                client = get_dashscope_client()
                # DashScope video gen
                dp = {
                    "model": params.get("model", "wanx-v1"),
                    "input": {"prompt": params.get("prompt")}
                }
                # Adapter for size/ratio?
                response = await client.generate_video(dp, wait=True)
                if not response.is_succeeded:
                     raise Exception(f"DashScope T2V failed: {response.message}")
                return {"status": "succeeded", "result_url": response.video_url, "data": response.model_dump(), "provider": provider}

            else:
                raise ValueError(f"Provider '{provider}' not supported for text-to-video")

        except Exception as e:
            logger.error(f"{provider} T2V failed: {e}")
            raise e


@registry.register("image-to-video")
class ImageToVideoHandler(BaseHandler):
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return True

    async def execute(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        params = task.get("params", {})
        provider = params.get("provider", config.DEFAULT_VIDEO_PROVIDER).lower()
        
        logger.info(f"Executing Image-to-Video via {provider}")
        
        try:
            # --- VolcEngine ---
            if provider == "volcengine":
                client = get_volc_client()
                async def callback(resp):
                    await context.update_status("processing", result={"api_status": resp.status})
                
                if "content" not in params and "image_url" in params:
                    content = [{"type": "image_url", "image_url": params["image_url"]}]
                    if "prompt" in params:
                        content.append({"type": "text", "text": params["prompt"]})
                    params["content"] = content

                response = await client.generate_video(params, wait=True, callback=callback)
                if response.status != "succeeded":
                    raise Exception(f"Video generation failed: {response.status}")
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- Baidu ---
            elif provider == "baidu":
                client = get_baidu_client()
                bp = {
                    "model": params.get("model", "stable-video-diffusion"),
                    "taskInput": {"image": params.get("image_url") or params.get("image")}
                }
                if "prompt" in params: bp["taskInput"]["text"] = params["prompt"]
                
                response = await client.image_to_video(bp, wait=True)
                if not response.is_succeeded:
                     raise Exception(f"Baidu I2V failed")
                return {"status": "succeeded", "data": response.model_dump(), "provider": provider}

            # --- MiniMax ---
            elif provider == "minimax":
                client = get_minimax_client()
                # I2V via same generating endpoint but with first_frame_image
                mp = {
                    "model": params.get("model", "video-01"),
                    "prompt": params.get("prompt", "generate video from image"),
                    "first_frame_image": params.get("image_url")
                }
                response = await client.generate_video(mp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"MiniMax I2V failed")
                return {"status": "succeeded", "result_url": response.download_url, "data": response.model_dump(), "provider": provider}
            
            # --- Kling ---
            elif provider == "kling":
                client = get_kling_client()
                kp = {
                    "model": params.get("model", "kling-v1"),
                    "image": params.get("image_url"), # Kling param name for I2V
                    "prompt": params.get("prompt", "") # optional
                }
                response = await client.image_to_video(kp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"Kling I2V failed")
                video_url = response.data.task_result.videos[0].url if response.data.task_result and response.data.task_result.videos else None
                return {"status": "succeeded", "result_url": video_url, "data": response.model_dump(), "provider": provider}

            # --- DashScope ---
            elif provider == "dashscope":
                client = get_dashscope_client()
                dp = {
                    "model": params.get("model", "wanx-v1"),
                    "input": {
                        "prompt": params.get("prompt", ""),
                        "img_url": params.get("image_url")
                    }
                }
                response = await client.generate_video(dp, wait=True)
                if not response.is_succeeded:
                    raise Exception(f"DashScope I2V failed")
                return {"status": "succeeded", "result_url": response.video_url, "data": response.model_dump(), "provider": provider}

            else:
                 raise ValueError(f"Provider '{provider}' not supported for image-to-video")

        except Exception as e:
            logger.error(f"{provider} I2V failed: {e}")
            raise e

             
@registry.register("video-to-video")
class VideoToVideoHandler(BaseHandler):
    # Placeholder for future expansion
     def validate_params(self, params: Dict[str, Any]) -> bool:
        return True
     async def execute(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
         params = task.get("params", {})
         provider = params.get("provider", "").lower()
         
         if provider == "baidu":
             client = get_baidu_client()
             bp = {
                 "model": params.get("model", "video_style_conversion"),
                 "taskInput": {
                     "video": params.get("video_url"),
                     "style": params.get("style", "cyberpunk")
                     # prompt is optiona usually for style conversion
                 }
             }
             if "prompt" in params: bp["taskInput"]["prompt"] = params["prompt"]
             
             response = await client.video_to_video(bp, wait=True)
             if not response.is_succeeded:
                 raise Exception("Baidu V2V failed")
             return {"status": "succeeded", "data": response.model_dump(), "provider": provider}
             
         raise NotImplementedError(f"Video-to-Video not fully configured for {provider}")

