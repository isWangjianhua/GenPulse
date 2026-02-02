# 如何添加新的 Provider

本指南说明如何使用我们要准的 Client-Handler 架构向 GenPulse 系统添加新的 AI 能力提供商（例如 "Sora" 或 "DeepSeek"）。

## 1. 概述

添加提供商涉及四个主要步骤：
1.  **定义 Schema**: 创建 Request/Response Pydantic 模型。
2.  **实现 Client**: 继承 `BaseClient` 以处理 HTTP/WebSocket 交互。
3.  **注册 Handler**: 更新 Feature Handler 以将请求路由到您的新客户端。
4.  **配置**: 将 API Key 添加到 `.env`。

---

## 2. 逐步实现

### 步骤 1: 定义 Schema (`schemas.py`)

创建 `src/genpulse/clients/<provider>/schemas.py`。
严格定义输入参数和 API 响应结构。

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

### 步骤 2: 实现 Client (`client.py`)

创建 `src/genpulse/clients/<provider>/client.py`。
继承 `BaseClient`。

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
        # 1. 转换为 Dict
        data = params.model_dump(exclude_none=True)
        
        # 2. 发起请求
        resp_json = await self._request("POST", "/generations", json=data)
        
        # 3. 处理轮询 (如果是异步)
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

### 步骤 3: 更新 Handler

编辑相关的 Handler (例如 `src/genpulse/handlers/image.py`)。

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
            # 验证并转换参数
            params = MyProviderImageParams.model_validate(task["params"])
            
            result = await client.generate_image(params)
            
            return {
                "status": "succeeded",
                "result_url": result["output_url"],
                "provider": "myprovider"
            }
```

### 步骤 4: 配置

将 API Key 添加到 `.env` 和 `src/genpulse/config.py`。

```python
# config.py
MYPROVIDER_API_KEY = settings.get("MYPROVIDER_API_KEY")
```

---

## 3. 检查清单

- [ ] Schema 的所有字段都有 `description` (未来用于 Auto-UI)。
- [ ] Client 继承自 `BaseClient`。
- [ ] 轮询逻辑使用 `self.poll_task`。
- [ ] Handler 在方法内部 import Client (懒加载)，以避免依赖缺失导致启动错误。
- [ ] 抛出有意义的错误信息。
