# Initial Scaffold Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Create the initial project structure for GenPulse, including the directory layout, core FastAPI application, Redis connection, and the `manager.py` entry point, based on `architecture_design.md`.

**Architecture:**
- **FastAPI** as the web framework.
- **Redis** for the task queue.
- **Manager.py** as the Unified CLI for starting services.
- **Registry Pattern** for Handlers.

**Tech Stack:** Python 3.10+, FastAPI, Redis, Uvicorn, Click (for CLI).

---

### Task 1: Project Skeleton & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `core/__init__.py`
- Create: `handlers/__init__.py`
- Create: `libs/comfyui/.gitkeep`
- Create: `clients/__init__.py`

**Step 1: Create requirements.txt**

```text
fastapi
uvicorn
redis
pydantic
python-dotenv
click
httpx
sqlalchemy
asyncpg
```

**Step 2: Create Directory Structure**

Run:
```bash
mkdir -p core handlers libs/comfyui clients docs/plans
touch core/__init__.py handlers/__init__.py clients/__init__.py libs/comfyui/.gitkeep
```

**Step 3: Install Dependencies**

Run:
```bash
pip install -r requirements.txt
```
(If pip is not available, ensure python environment is set up. As this is a plan, we assume standard python env).

---

### Task 2: Core Redis MQ Wrapper

**Files:**
- Create: `core/mq.py`
- Test: `tests/core/test_mq.py` (Simple connection test)

**Step 1: Write the failing test**

Create `tests/core/test_mq.py`:
```python
import pytest
from core.mq import RedisManager

@pytest.mark.asyncio
async def test_redis_connection():
    redis = RedisManager()
    assert await redis.ping()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_mq.py`
Expected: FAIL (ModuleNotFoundError or ImportError)

**Step 3: Write minimal implementation**

Create `core/mq.py`:
```python
import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

class RedisManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = redis.from_url(self.redis_url, decode_responses=True)

    async def ping(self):
        return await self.client.ping()

    async def push_task(self, task_data: str):
        await self.client.lpush("tasks:pending", task_data)

    async def pop_task(self):
        # Blocking pop
        return await self.client.brpop("tasks:pending", timeout=1)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_mq.py`
(Note: Requires running Redis instance. If no Redis, we might need `fakeredis` for testing, but for now we assume dev env has one or we mock it. For this plan, let's assume `fakeredis` or skip if no env.)

Better: Add `fakeredis` to requirements for testing.

---

### Task 3: Core Gateway & Registry

**Files:**
- Create: `core/gateway.py`
- Create: `handlers/base.py`

**Step 1: Define BaseHandler**

Create `handlers/base.py`:
```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseHandler(ABC):
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass
```

**Step 2: Create Gateway (FastAPI App)**

Create `core/gateway.py`:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

app = FastAPI(title="GenPulse API")

class TaskRequest(BaseModel):
    task_type: str
    params: Dict[str, Any]
    priority: str = "normal"

@app.post("/task")
async def create_task(req: TaskRequest):
    # Minimal stub
    task_id = str(uuid.uuid4())
    return {"task_id": task_id, "status": "pending", "message": "Task received"}

@app.get("/status")
async def health_check():
    return {"status": "ok"}
```

---

### Task 4: Unified CLI (Manager)

**Files:**
- Create: `manager.py`

**Step 1: Create manager.py**

Create `manager.py`:
```python
import click
import uvicorn
import subprocess
import os

@click.group()
def cli():
    pass

@cli.command()
def start_api():
    """Start only the API Server"""
    print("Starting API Server...")
    uvicorn.run("core.gateway:app", host="0.0.0.0", port=8000, reload=True)

@cli.command()
def start_worker():
    """Start only the Worker"""
    print("Starting Worker... (Stub)")
    # Logic to start worker loop
    pass

@cli.command()
def start_all():
    """Start API, Worker, and Local Libs (Dev Mode)"""
    print("Starting All Services in Hybrid Mode...")
    
    # 1. Start ComfyUI (Stub for now)
    comfy_path = os.path.join("libs", "comfyui", "main.py")
    if os.path.exists(comfy_path):
        print(f"Launching Local ComfyUI from {comfy_path}...")
        # subprocess.Popen(["python", comfy_path])
    else:
        print("Local ComfyUI not found, skipping...")

    # 2. Start API
    # In a real shell script we'd background them, here in python we might need multiprocessing
    # For simplicity in this plan, we just launch API as the blocker
    print("Starting API...")
    uvicorn.run("core.gateway:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    cli()
```
