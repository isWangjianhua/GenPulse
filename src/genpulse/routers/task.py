from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Literal
import uuid
import json
from loguru import logger
from genpulse.infra.mq import get_mq
from genpulse.infra.database.manager import DBManager
from genpulse import config

router = APIRouter(prefix="/task", tags=["tasks"])
mq = get_mq()

# from genpulse.types import TaskRequest (Deprecated)
from genpulse.schemas.request import TaskRequest

from genpulse.utils.upload_helper import process_base64_inputs

@router.post("")
async def create_task(req: TaskRequest):
    task_id = str(uuid.uuid4())
    
    # 0. Handle Base64 Uploads
    # Convert params to dict and scan for Base64 Data URIs to upload
    raw_params = req.params.model_dump()
    processed_params = await process_base64_inputs(raw_params)
    
    # 1. Persist to DB
    try:
        await DBManager.create_task(task_id, req.task_type, processed_params)
    except Exception as e:
        logger.error(f"DB Error: {e}")
    
    # 2. Push to MQ
    task_data = {
        "task_id": task_id,
        "task_type": req.task_type,
        "provider": req.provider,
        "params": processed_params,
        "priority": req.priority,
        "callback_url": req.callback_url
    }
    
    try:
        await mq.push_task(json.dumps(task_data))
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Task received and queued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MQ Error: {str(e)}")

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    # 1. Try MQ Cache
    data = await mq.get_task_status(task_id)
    if data:
        return data
        
    # 2. Try DB
    task = await DBManager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "task_type": task.task_type
    }

@router.get("")
async def list_tasks(limit: int = 50):
    tasks = await DBManager.list_tasks(limit=limit)
    return [{
        "task_id": t.task_id,
        "task_type": t.task_type,
        "status": t.status,
        "progress": t.progress,
        "created_at": t.created_at
    } for t in tasks]
