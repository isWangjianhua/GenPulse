import uuid
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from fastapi.staticfiles import StaticFiles
from core.mq import RedisManager
from core.db_manager import DBManager
from core.config import settings
import os

app = FastAPI(title="GenPulse API")

# Mount static files for assets
os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
app.mount("/assets", StaticFiles(directory=settings.STORAGE_LOCAL_PATH), name="assets")

redis_mgr = RedisManager()

class TaskRequest(BaseModel):
    task_type: str
    params: Dict[str, Any]
    priority: str = "normal"

@app.post("/task")
async def create_task(req: TaskRequest):
    task_id = str(uuid.uuid4())
    
    # 1. Persist to DB
    try:
        await DBManager.create_task(task_id, req.task_type, req.params)
    except Exception as e:
        # Fallback or log if DB is down, we still want to try MQ if DB is optional
        print(f"DB Error: {e}")
        # In a strict system, we might raise HTTPException(500)
    
    # 2. Push to MQ
    task_data = {
        "task_id": task_id,
        "task_type": req.task_type,
        "params": req.params,
        "priority": req.priority
    }
    
    try:
        await redis_mgr.push_task(json.dumps(task_data))
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Task received and queued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis Error: {str(e)}")

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    from core.config import settings
    status_key = f"{settings.redis_prefix}task_status:{task_id}"
    data = await redis_mgr.client.get(status_key)
    if not data:
        raise HTTPException(status_code=404, detail="Task not found or expired")
    return json.loads(data)

@app.get("/health")
async def health_check():
    try:
        await redis_mgr.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)}

@app.get("/")
async def root():
    return {"message": "GenPulse API is running"}
