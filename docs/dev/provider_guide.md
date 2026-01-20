# How to Add a New Provider

This guide explains how to add a new AI capabilities provider (e.g., integrating DeepSeek for text, or Luma for video) to the GenPulse system.

## 1. Overview

Adding a provider involves three main steps:
1.  **Client Wrapper**: Create a low-level API client (optional, but recommended).
2.  **Engine Implementation**: Implement the `BaseEngine` interface.
3.  **Handler Routing**: Update the Feature Handler to route requests to your new engine.

## 2. Step-by-Step

### Step 1: Create the Client (Optional)

If you are calling an external API, wrap it in a client class inheriting from `BaseClient`.

```python
# src/genpulse/clients/myprovider/client.py
from genpulse.clients.base import BaseClient

class MyProviderClient(BaseClient):
    async def generate_something(self, prompt: str):
        return await self._request("POST", "/generate", json={"prompt": prompt})
```

### Step 2: Implement the Engine

Create a new engine in `src/genpulse/engines/`. It **must** inherit from `BaseEngine` and use `TaskContext`.

```python
# src/genpulse/engines/my_engine.py
from genpulse.engines.base import BaseEngine
from genpulse.types import TaskContext, EngineError
class MyEngine(BaseEngine):
    def validate_params(self, params):
        return "prompt" in params

    async def execute(self, task, context: TaskContext):
        try:
            # 1. Update status
            await context.set_processing(progress=10, info="Starting...")
            
            # 2. Call your logic/client
            # ...
            
            # 3. Return result
            return {"data": "..."}
            
        except Exception as e:
            # Wrap errors for specific reporting
            raise EngineError(f"MyProvider failed: {e}", provider="myprovider")
```

### Step 3: Update the Handler

Edit the relevant handler (e.g., `src/genpulse/features/image/handlers.py`) to instantiate your engine when the user requests this provider.

```python
# src/genpulse/features/image/handlers.py

# ... inside TextToImageHandler.execute ...
provider = params.get("provider")

if provider == "myprovider":
    from genpulse.engines.my_engine import MyEngine
    return await MyEngine().execute(task, context)
```

### Step 4: Configuration

Add any API Keys or URLs to `src/genpulse/config.py` using `settings.get()`.

```python
# config.py
MYPROVIDER_API_KEY = settings.get("MYPROVIDER_API_KEY")
```

## 3. Checklist

- [ ] Engine inherits from `BaseEngine`.
- [ ] `execute` method signature uses `TaskContext`.
- [ ] Exceptions are wrapped in `EngineError`.
- [ ] Integration test added in `tests/engines/`.
