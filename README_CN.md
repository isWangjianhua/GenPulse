# GenPulse

> **高并发生成式 AI 后端系统**

GenPulse 是一个基于 Agentic 架构和事件驱动模式的后端系统，专为大规模编排复杂的生成式 AI 工作流（图像、视频、音频）而设计。它通过摄入、编排与执行的分离架构，确保了极高的可靠性与可观测性。

---

## 🚀 核心特性

*   **Agentic 架构**：系统组件被设计为具有高度自主性的 Agent（摄入、编排、执行）。
*   **双重状态同步**：通过 Redis 实现毫秒级实时状态更新，利用 PostgreSQL 确保数据持久化与审计能力。
*   **统一存储层**：抽象的资产管理层，支持 **本地存储**（开发环境）与 **S3/OSS**（生产环境）无缝切换。
*   **可扩展插件系统**：支持插件化的执行代理。当前已内置 **ComfyUI Handler**，用于处理复杂的节点式图像生成任务。
*   **现代化技术栈**：基于 **FastAPI**, **Redis**, **SQLAlchemy (Async)** 构建，并使用 **uv** 进行包管理。

---

## 🏗️ 架构设计

系统遵循严格的关注点分离原则，详见 [AGENTS.md](./AGENTS.md)：

1.  **Ingestion Agent** (`Gateway`): 负责请求校验与初始状态持久化。
2.  **Orchestration Agent** (`Worker`): 轮询队列并将任务分发给领域专家 Agent。
3.  **Execution Agents** (`Handlers`): 封装具体 AI 引擎逻辑（如 ComfyHandler，StableDiffusionHandler）。

---

## 🛠️ 快速开始

### 前置要求

*   **Python 3.12+**
*   **uv** (高性能 Python 包管理器)
*   **PostgreSQL** (数据库)
*   **Redis** (消息队列)
*   *(可选)* **ComfyUI** 实例 (用于运行图像生成任务)

### 安装步骤

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/your-org/genpulse.git
    cd genpulse
    ```

2.  **安装依赖**:
    ```bash
    uv sync
    ```

3.  **环境变量配置**:
    复制并创建 `.env` 文件：

    ```ini
    ENV=dev
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/genpulse
    REDIS_URL=redis://localhost:6379/0
    
    # 存储配置 (选项: local, s3)
    STORAGE_TYPE=local
    STORAGE_LOCAL_PATH=data/assets
    
    # S3/OSS 配置 (可选)
    # S3_ENDPOINT_URL=https://oss-cn-hangzhou.aliyuncs.com
    # S3_ACCESS_KEY=xxx
    # S3_SECRET_KEY=xxx
    # S3_BUCKET_NAME=genpulse
    ```

4.  **初始化数据库**:
    ```bash
    # 请确保 PostgreSQL 服务已启动
    uv run alembic upgrade head
    ```

### 启动系统

你可以单独启动各组件，或通过即将推出的 manager 统一管理。

**1. 启动网关 (API)**
```bash
uv run uvicorn core.gateway:app --reload
```

**2. 启动执行器 (Orchestrator)**
```bash
uv run python -m core.worker
```

---

## 💡 使用指南

### 提交 ComfyUI 任务

GENPULSE 允许你提交 ComfyUI 工作流，系统会自动调度执行并返回托管的结果 URL。

**请求示例:**
```http
POST /task
Content-Type: application/json

{
  "task_type": "comfyui",
  "params": {
    "server_address": "127.0.0.1:8188",
    "workflow": { ... } // ComfyUI API JSON 格式
  }
}
```

**响应示例:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Task received and queued"
}
```

**查询状态:**
```http
GET /task/550e8400-e29b-41d4-a716-446655440000
```

---

## 👨‍💻 开发规范

我们遵循严格的 **Dev -> Test -> Main** 工作流。

-   **`dev`**: 主开发分支。
-   **`test`**: 集成测试 / 准生产环境。
-   **`main`**: 生产发布分支。

**运行测试**:
```bash
uv run pytest
```

更多关于角色分工与协议细节，请阅读 **[AGENTS.md](./AGENTS.md)**。
