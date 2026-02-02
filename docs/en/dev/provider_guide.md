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
    
    # Allow extra fields (like 'provider') to be passed without error
    model_config = ConfigDict(extra='ignore')

# ... (Client implementation is fine) ...

# src/genpulse/handlers/image.py

@registry.register("text-to-image")
class TextToImageHandler(BaseHandler):
    async def execute(self, task, context):
        provider = task["params"].get("provider")
        
        if provider == "myprovider":
            # Lazy import to avoid circular deps or missing optional libs
            from genpulse.clients.myprovider.client import create_myprovider_client
            from genpulse.clients.myprovider.schemas import MyProviderImageParams
            
            client = create_myprovider_client()
            
            # Use model_validate to parse dict
            try:
                params = MyProviderImageParams.model_validate(task["params"])
            except ValidationError as e:
                raise ValueError(f"Invalid parameters: {e}")
            
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
