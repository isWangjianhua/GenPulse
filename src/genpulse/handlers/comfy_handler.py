import asyncio
import io
import uuid
import json
from typing import Any, Dict, List, Optional
from loguru import logger

from genpulse.handlers.base import BaseHandler
from genpulse.handlers.registry import registry
from genpulse.types import TaskContext, EngineError
from genpulse import config
from genpulse.infra.storage import get_storage
from genpulse.clients.comfyui.client import ComfyClient, ComfyClientError

# Import our new template helpers
from genpulse.utils.comfy import parse_workflow_template, apply_params, load_template

@registry.register("comfy-workflow")
class ComfyUIHandler(BaseHandler):
    """
    Refactored ComfyUI Handler.
    Leverages ComfyClient for communication and Template system for workflow generation.
    """
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        if "workflow" not in params and "template_name" not in params:
            logger.error("ComfyUIHandler: Neither 'workflow' nor 'template_name' provided.")
            return False
        return True

    async def execute(self, task_data: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        params = task_data.get("params", {})
        
        # 1. Determine Server Address
        server_address = params.get("server_address", config.COMFY_URL or "http://127.0.0.1:8188")
        
        # 2. Prepare Workflow
        workflow = {}
        inputs = params.get("inputs", {})
        
        try:
            if "template_name" in params:
                template_name = params["template_name"]
                logger.info(f"Loading ComfyUI Template: {template_name}")
                workflow_template = load_template(template_name)
                
                # Auto-inject params
                # We merge top-level params (like prompt) into inputs if not present
                system_keys = {"provider", "template_name", "server_address", "workflow", "inputs"}
                merged_inputs = {k: v for k, v in params.items() if k not in system_keys}
                merged_inputs.update(inputs) 
                
                # Parse schema from template to find dynamic fields
                schema = parse_workflow_template(workflow_template)
                workflow = apply_params(workflow_template, merged_inputs, schema)
                
            elif "workflow" in params:
                # Raw mode
                workflow = params["workflow"]
                schema = parse_workflow_template(workflow)
                workflow = apply_params(workflow, inputs, schema)
            else:
                raise EngineError("No valid workflow definition found", provider="comfyui")
                
        except Exception as e:
            raise EngineError(f"Workflow preparation failed: {e}", provider="comfyui")

        # 3. Execution
        client = ComfyClient(base_url=server_address)
        storage = get_storage()
        images_result = []
        prompt_id = None
        
        # Simple health check
        if not await client.check_health():
             # Try one more time? or just fail.
             logger.warning(f"ComfyUI at {server_address} seems unreachable, trying anyway...")

        try:
            # Quit Prompt
            prompt_id = await client.queue_prompt(workflow)
            logger.info(f"ComfyUI Queued: {prompt_id}")
            await context.set_processing(10, info="Queued")
            
            # Listen for progress via Client Generator
            async for msg in client.listen_progress(prompt_id):
                if msg["type"] == "progress":
                    val = msg.get("value", 0)
                    m = msg.get("max", 1)
                    if m > 0:
                        p = 10 + int((val / m) * 80) # Map 0-100 to 10-90
                        node = msg.get("node", "?")
                        await context.set_processing(p, info=f"Running Node {node}")
                
                elif msg["type"] == "binary_image":
                    # Instant upload of WS image (SaveImageWebsocket)
                    img_data = msg["data"]
                    fname = f"comfy/{task_data['task_id']}/{uuid.uuid4()}.png"
                    url = await storage.upload(fname, io.BytesIO(img_data), content_type="image/png")
                    images_result.append(url)
                    logger.info(f"Captured binary image: {url}")
                
                elif msg["type"] == "error":
                     raise EngineError(f"ComfyUI WS Error: {msg['message']}", provider="comfyui")
            
            # 4. Fallback: If no binary images captured, check history (Standard SaveImage Node)
            if not images_result:
                logger.info("No WS images captured, checking history for outputs...")
                history = await client.get_history(prompt_id)
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    for _, output_val in outputs.items():
                         if "images" in output_val:
                             for img in output_val["images"]:
                                 fname = img["filename"]
                                 subfolder = img["subfolder"]
                                 ftype = img["type"]
                                 # Use client helper to fetch raw bytes
                                 raw = await client.get_image(fname, subfolder, ftype)
                                 
                                 s3_key = f"comfy/{task_data['task_id']}/{fname}"
                                 url = await storage.upload(s3_key, io.BytesIO(raw), content_type="image/png")
                                 images_result.append(url)

        except ComfyClientError as e:
            raise EngineError(f"ComfyUI Client Error: {e}", provider="comfyui")
        except Exception as e:
            logger.exception("ComfyUI Execution Failed")
            raise EngineError(f"Unexpected Error: {e}", provider="comfyui")

        await context.set_processing(100, info="Completed")
        
        return {
            "prompt_id": prompt_id,
            "images": images_result,
            "image_url": images_result[0] if images_result else None,
            "count": len(images_result)
        }
