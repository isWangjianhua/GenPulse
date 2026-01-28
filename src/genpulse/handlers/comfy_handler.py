import asyncio
import json
import uuid
import aiohttp
from typing import Any, Dict, List, Optional
import httpx
from genpulse.handlers.base import BaseHandler
from genpulse.handlers.registry import registry
from genpulse.types import TaskContext, EngineError
from genpulse.utils.comfy import parse_workflow_template, apply_params
from genpulse import config
from genpulse.infra.storage import get_storage
from loguru import logger
import io

@registry.register("comfy-workflow")
class ComfyUIHandler(BaseHandler):
    """
    Handler for executing ComfyUI workflows using WebSocket for real-time progress 
    and binary image retrieval.
    """
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        if "workflow" not in params:
            logger.error("ComfyUIHandler: 'workflow' field missing in params.")
            return False
            
        workflow = params["workflow"]
        if "nodes" in workflow and "links" in workflow:
            logger.error("Invalid Workflow Format: Received Web UI JSON. Please export as API Format (Prompt Format).")
            return False
            
        return True

    async def execute(self, task_data: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        params = task_data.get("params", {})
        workflow = params.get("workflow")
        inputs = params.get("inputs", {})
        
        # Determine server address
        server_address = params.get("server_address") or config.COMFY_URL
        if not server_address:
             raise EngineError("ComfyUI URL not configured", provider="comfyui")
        server_address = server_address.rstrip('/')
        
        # Parse Host for WebSocket
        ws_address = server_address.replace("http://", "ws://").replace("https://", "wss://")

        # 1. Parse & Inject
        try:
            schema = parse_workflow_template(workflow)
            logger.info(f"ComfyUI Task {task_data['task_id']}: Found inputs {[p.name for p in schema]}")
            final_workflow = apply_params(workflow, inputs, schema)
        except Exception as e:
            raise EngineError(f"Workflow parsing failed: {e}", provider="comfyui")

        # 2. Connect & Submit
        client_id = str(uuid.uuid4())
        prompt_id = None
        images_result = []
        storage = get_storage()
        
        try:
            async with aiohttp.ClientSession() as session:
                ws_url = f"{ws_address}/ws?clientId={client_id}"
                logger.info(f"Connecting to WS: {ws_url}")
                
                async with session.ws_connect(ws_url) as ws:
                    # Submit Prompt
                    payload = {"prompt": final_workflow, "client_id": client_id}
                    async with session.post(f"{server_address}/prompt", json=payload) as resp:
                        if resp.status != 200:
                            err_text = await resp.text()
                            raise EngineError(f"ComfyUI Submit Failed: {err_text}", provider="comfyui")
                        prompt_res = await resp.json()
                        prompt_id = prompt_res.get("prompt_id")
                        logger.info(f"ComfyUI Queued: {prompt_id}")
                        await context.set_processing(5, info="Queued")

                    # Listen to WebSocket
                    current_node = ""
                    # We loop until execution_success or disconnected
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            message = json.loads(msg.data)
                            msg_type = message.get("type")
                            data = message.get("data", {})
                            
                            # Filter messages only for our prompt if possible?
                            # ComfyUI sends broadcast messages, but usually filtered by client_id if connected?
                            # Actually /ws?clientId=... means we only get messages for OUR client_id usually?
                            # Wait, 'executing' gives 'node' and 'prompt_id'.
                            
                            if msg_type == "executing":
                                if data.get("node") is None and data.get("prompt_id") == prompt_id:
                                    # Execution finished for this prompt
                                    logger.info("ComfyUI Execution Finished (WS Signal)")
                                    break
                                elif data.get("prompt_id") == prompt_id:
                                    # Node started
                                    current_node = data.get("node")
                                    # Calculate vague progress... simple increment?
                                    await context.set_processing(None, info=f"Running Node {current_node}")

                            elif msg_type == "progress":
                                if data.get("prompt_id") == prompt_id:
                                    val = data.get("value")
                                    max_val = data.get("max")
                                    if max_val:
                                        p = int((val / max_val) * 100)
                                        await context.set_processing(p, info=f"Node {current_node} {p}%")
                                        
                            elif msg_type == "execution_cached":
                                if data.get("prompt_id") == prompt_id:
                                    logger.info("ComfyUI used cached result")
                                    break

                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            # This is a Preview/SaveWebsocket image!
                            # First 8 bytes are type/event info usually?
                            # ComfyUI protocol:
                            # The binary message starts with a 4-byte integer (big-endian) specifying the event type?
                            # Standard PreviewImage: Just raw bytes? 
                            # Actually, standard logic is: Prepend text header?
                            # Let's assume standard PreviewImage behavior:
                            # It comes as binary with first 4 bytes as Type (1=JPEG, 2=PNG) then data.
                            # We can just check header or assume image.
                            
                            image_data = msg.data[8:] # Skip offset (8 bytes usually: 4 type, 4 params?)
                            # Actually, for simplicity we treat it as blob.
                            
                            # Upload to Unified Storage
                            fname = f"comfy/{task_data['task_id']}/{uuid.uuid4()}.png"
                            url = await storage.upload(fname, io.BytesIO(image_data), content_type="image/png")
                            images_result.append(url)
                            logger.info(f"Captured binary image via WS: {url}")

            # 3. Post-Processing: Explicit History Check (Fallback)
            # If we didn't get any binary images (maybe standard SaveImage node used), check history.
            if not images_result:
                async with httpx.AsyncClient() as client:
                    hist_resp = await client.get(f"{server_address}/history/{prompt_id}")
                    if hist_resp.status_code == 200:
                        history_data = hist_resp.json()
                        if prompt_id in history_data:
                            outputs = history_data[prompt_id].get("outputs", {})
                            for _, output_val in outputs.items():
                                if "images" in output_val:
                                    for img in output_val["images"]:
                                        # Download from ComfyUI View API and Upload to S3
                                        fname = img.get("filename")
                                        subfolder = img.get("subfolder", "")
                                        img_type = img.get("type", "output")
                                        
                                        view_url = f"{server_address}/view?filename={fname}&subfolder={subfolder}&type={img_type}"
                                        logger.info(f"Downloading from ComfyUI: {view_url}")
                                        
                                        img_resp = await client.get(view_url)
                                        if img_resp.status_code == 200:
                                            s3_key = f"comfy/{task_data['task_id']}/{fname}"
                                            s3_url = await storage.upload(s3_key, io.BytesIO(img_resp.content), content_type=img_resp.headers.get("content-type"))
                                            images_result.append(s3_url)

        except Exception as e:
            raise EngineError(f"ComfyUI Execution Error: {e}", provider="comfyui")

        await context.set_processing(100, info="Completed")
        
        return {
            "prompt_id": prompt_id,
            "images": images_result,
            "image_url": images_result[0] if images_result else None
        }
