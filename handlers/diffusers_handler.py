import io
import torch
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional
from handlers.base import BaseHandler
from core.storage import get_storage
from core.registry import registry

# Try to import diffusers, if not available yet (still installing), we'll handle it during execution
try:
    from diffusers import StableDiffusionPipeline
except ImportError:
    StableDiffusionPipeline = None

logger = logging.getLogger(__name__)

# Global cache for pipelines to avoid reloading
_pipeline_cache: Dict[str, Any] = {}

def get_pipeline(model_id: str, device: str = "auto") -> Any:
    global _pipeline_cache
    if model_id in _pipeline_cache:
        return _pipeline_cache[model_id]
    
    if StableDiffusionPipeline is None:
        raise ImportError("diffusers is not installed")
    
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Loading diffusers model: {model_id} on {device}")
    
    # Load pipeline
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id, 
        torch_dtype=dtype,
        use_safetensors=True
    )
    pipe.to(device)
    
    # Optional: performance boosts
    if device == "cuda":
        # pipe.enable_xformers_memory_efficient_attention() # requires xformers
        pipe.enable_attention_slicing()
        
    _pipeline_cache[model_id] = pipe
    return pipe

@registry.register("diffusers_txt2img")
class DiffusersHandler(BaseHandler):
    def validate_params(self, params: Dict[str, Any]) -> bool:
        if "prompt" not in params:
            logger.error("Missing 'prompt' in params")
            return False
        return True

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        params = task.get("params", {})
        model_id = params.get("model_id", "runwayml/stable-diffusion-v1-5")
        prompt = params["prompt"]
        negative_prompt = params.get("negative_prompt", "")
        steps = params.get("steps", 30)
        guidance_scale = params.get("guidance_scale", 7.5)
        seed = params.get("seed")
        
        update_status = context["update_status"]
        storage = get_storage()
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        loop = asyncio.get_running_loop()
        
        try:
            # 1. Load Pipeline
            await update_status("processing", progress=5, result={"info": f"Loading model {model_id}"})
            pipe = await loop.run_in_executor(None, lambda: get_pipeline(model_id, device=device))
            
            # 2. Setup Generator
            generator = None
            if seed is not None:
                generator = torch.Generator(device=device).manual_seed(seed)
            
            # 3. Progress Callback Wrapper
            def callback(step: int, timestep: int, latents: Any):
                # Calculate progress (10% to 85%)
                p = 10 + int((step / steps) * 75)
                # We can't await here because this is a sync callback from diffusers
                # We use loop.call_soon_threadsafe to schedule the async update
                coro = update_status("processing", progress=p)
                asyncio.run_coroutine_threadsafe(coro, loop)

            # 4. Run Inference in Thread
            await update_status("processing", progress=10, result={"info": "Starting inference"})
            
            def run_inference():
                return pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                    callback=callback,
                    callback_steps=max(1, steps // 5) # Update every 1/5th of the way
                ).images[0]

            image = await loop.run_in_executor(None, run_inference)
            
            # 5. Upload result
            await update_status("processing", progress=90, result={"info": "Uploading result"})
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            file_path = f"{task['task_id']}/diff_out_{uuid.uuid4().hex[:8]}.png"
            url = await storage.upload(file_path, img_byte_arr, content_type="image/png")
            
            return {
                "model_id": model_id,
                "images": [url],
                "count": 1,
                "params": {
                    "steps": steps,
                    "guidance_scale": guidance_scale,
                    "seed": seed
                }
            }
            
        except Exception as e:
            logger.error(f"Diffusers execution failed: {e}")
            raise
