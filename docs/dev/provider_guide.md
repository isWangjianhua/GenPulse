# How to Add a New Provider

This guide explains how to add a new AI capabilities provider (e.g., "Sora" or "DeepSeek") to the GenPulse system using our standard Client-Handler architecture.

## 1. Overview

Adding a provider involves four main steps:
1.  **Define Schemas**: Create Request/Response Pydantic models.
2.  **Implement Client**: Inherit from `BaseClient` to handle HTTP/WebSocket interactions.
3.  **Register Handler**: Update the Feature Handler to route requests to your new client.
4.  **Configuration**: Add API keys to `.env`.

---

## 2. Step-by-Step Implementation

### Step 1: Define Schemas (`schemas.py`)

Create `src/genpulse/clients/<provider>/schemas.py`.
Strictly define input parameters and API response structures.

```python
from pydantic import BaseModel, Field, ConfigDict

class MyProviderImageParams(BaseModel):
    prompt: str = Field(..., description="Image description")
    model: str = Field("v1", description="Model version")
    
    model_config = ConfigDict(populate_by_name=True)

class MyProviderResponse(BaseModel):
    id: str
    status: str
    output_url: str = Field(alias="url")
```

### Step 2: Implement the Client (`client.py`)

Create `src/genpulse/clients/<provider>/client.py`.
Inherit from `BaseClient`.

```python
from typing import Optional, Dict, Union
from genpulse.clients.base import BaseClient
from .schemas import MyProviderImageParams, MyProviderResponse

class MyProviderClient(BaseClient):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://api.myprovider.com/v1")
        self.api_key = api_key or "ENV_VAR"

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def generate_image(self, params: MyProviderImageParams, wait: bool = True):
        # 1. Convert Pydantic to Dict
        data = params.model_dump(exclude_none=True)
        
        # 2. Make Request
        resp_json = await self._request("POST", "/generations", json=data)
        
        # 3. Handle Polling (if async)
        task_id = resp_json["id"]
        
        if wait:
            return await self.poll_task(
                task_id=task_id,
                get_status_func=self.get_task,
                check_success_func=lambda r: r["status"] == "SUCCEEDED",
                check_failed_func=lambda r: r["status"] == "FAILED"
            )
        return resp_json

    async def get_task(self, task_id: str):
        return await self._request("GET", f"/generations/{task_id}")

def create_myprovider_client():
    return MyProviderClient()
```

### Step 3: Update the Handler

Edit the relevant handler (e.g., `src/genpulse/handlers/image.py`).

```python
# src/genpulse/handlers/image.py

@registry.register("text-to-image")
class TextToImageHandler(BaseHandler):
    async def execute(self, task, context):
        provider = task["params"].get("provider")
        
        if provider == "myprovider":
            from genpulse.clients.myprovider.client import create_myprovider_client
            from genpulse.clients.myprovider.schemas import MyProviderImageParams
            
            client = create_myprovider_client()
            params = MyProviderImageParams(**task["params"])
            
            result = await client.generate_image(params)
            
            return {
                "status": "succeeded",
                "result_url": result["output_url"],
                "provider": "myprovider"
            }
```

### Step 4: Configuration

Add any API Keys to `.env` and `src/genpulse/config.py`.

```python
# config.py
MYPROVIDER_API_KEY = settings.get("MYPROVIDER_API_KEY")
```

---

## 3. Checklist

- [ ] Schemas have `description` for all fields (for future Auto-UI).
- [ ] Client inherits from `BaseClient`.
- [ ] Polling logic uses `self.poll_task`.
- [ ] Handler imports Client inside the method (lazy import) to avoid startup errors if dependencies are missing.
- [ ] Meaningful error messages are raised.
