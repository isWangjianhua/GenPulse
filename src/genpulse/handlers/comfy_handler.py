import asyncio
import json
import uuid
from typing import Any, Dict, Optional
import httpx
from genpulse.handlers.base import BaseHandler
from genpulse.handlers.registry import registry
from genpulse.types import TaskContext, EngineError
from genpulse.utils.comfy import parse_workflow_template, apply_params
from genpulse import config
from loguru import logger

@registry.register("comfy-workflow")
class ComfyUIHandler(BaseHandler):
    """
    Handler for executing raw ComfyUI workflows appropriately parsed.
    """
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validates if the params contain a workflow.
        """
        if "workflow" not in params:
            logger.error("ComfyUIHandler: 'workflow' field missing in params.")
            return False
            
        # Optional: could run parse_workflow_template here to ensure it's valid JSON graph
        return True

    async def execute(self, task_data: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        """
        Executes a ComfyUI workflow.
        
        1. Parse template and inject inputs.
        2. Post to ComfyUI /prompt endpoint.
        3. Poll for completion or WebSocket (Simplified).
        """
        params = task_data.get("params", {})
        workflow = params.get("workflow")
        inputs = params.get("inputs", {})
        
        # Override server if provided per-req
        server_address = params.get("server_address") or config.COMFY_URL
        # Ensure url doesn't end with slash
        server_address = server_address.rstrip('/')

        # 1. Parse & Inject
        try:
            # We re-parse here to find dynamic inputs (logging purposes mostly or validation)
            schema = parse_workflow_template(workflow)
            logger.info(f"ComfyUI Task {task_data['task_id']}: Found inputs {[p.name for p in schema]}")
            
            final_workflow = apply_params(workflow, inputs, schema)
        except Exception as e:
            raise EngineError(f"Workflow parsing failed: {e}", provider="comfyui")

        # 2. Submit to ComfyUI
        client_id = str(uuid.uuid4())
        payload = {
            "prompt": final_workflow,
            "client_id": client_id
        }
        
        prompt_id = None
        images_result = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 2.1 Queue Prompt
                logger.info(f"Submitting to ComfyUI at {server_address}")
                resp = await client.post(f"{server_address}/prompt", json=payload)
                resp.raise_for_status()
                prompt_res = resp.json()
                prompt_id = prompt_res.get("prompt_id")
                
                if not prompt_id:
                     raise EngineError("ComfyUI did not return a prompt_id", provider="comfyui")
                     
                logger.info(f"ComfyUI Queued: {prompt_id}")
                await context.set_processing(10, info=f"Queued in ComfyUI as {prompt_id}")

                # 3. Wait for result (Simplified Polling)
                # In a real heavy-load system, we should use a WebSocket listener for ALL tasks.
                # For this implementation, we poll history or wait.
                # Since ComfyUI doesn't have a simple "poll status of prompt_id" easily without WS,
                # we will poll /history/{prompt_id}. If 404, it's pending. If 200, it's done.
                
                max_retries = 60 # 60 * 2s = 2 minutes timeout for demo
                for i in range(max_retries):
                    await asyncio.sleep(2)
                    
                    try:
                        hist_resp = await client.get(f"{server_address}/history/{prompt_id}")
                        if hist_resp.status_code == 200:
                            history_data = hist_resp.json()
                            if prompt_id in history_data:
                                # Completed!
                                data = history_data[prompt_id]
                                logger.info(f"ComfyUI Task Completed: {prompt_id}")
                                
                                # Extract Output Images
                                outputs = data.get("outputs", {})
                                for node_id, output_val in outputs.items():
                                    if "images" in output_val:
                                        for img in output_val["images"]:
                                            fname = img.get("filename")
                                            subfolder = img.get("subfolder", "")
                                            # Construct view URL
                                            # http://host/view?filename=...
                                            img_url = f"{server_address}/view?filename={fname}&subfolder={subfolder}&type={img.get('type')}"
                                            images_result.append(img_url)
                                
                                await context.set_processing(100, info="Completed")
                                break
                    except Exception as poll_err:
                        logger.warning(f"Polling error: {poll_err}")
                        
                    # Calculate artificial progress
                    await context.set_processing(10 + int((i/max_retries)*80))
                else:
                    raise EngineError("ComfyUI Task Timed Out (Polling)", provider="comfyui")

        except httpx.RequestError as e:
            raise EngineError(f"ComfyUI Network Error: {e}", provider="comfyui")
        except httpx.HTTPStatusError as e:
            raise EngineError(f"ComfyUI HTTP Error {e.response.status_code}: {e.response.text}", provider="comfyui")

        return {
            "prompt_id": prompt_id,
            "server": server_address,
            "images": images_result,
            # If unified storage is enabled, we should download these images and upload to S3 here.
            # But for this MVP, we return ComfyUI URLs.
            "image_url": images_result[0] if images_result else None
        }
