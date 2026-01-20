# GenPulse

> **高并发生成式 AI 后端系统**
>
> 🇺🇸 [English Documentation](./README.md)

GenPulse 是一个稳健的后端系统，专为大规模编排复杂的生成式 AI 工作流（图像、视频、音频）而设计。它为 AI 应用提供了可靠的任务调度、实时状态追踪以及统一的资产管理能力。

---

## 🚀 核心功能

*   **任务编排**：利用异步队列（Redis MQ）高效管理长耗时的 AI 生成任务。
*   **可靠的状态追踪**：采用“双重同步”机制——通过 Redis Pub/Sub 实现毫秒级更新，同时通过 PostgreSQL 保证数据的持久化与可审计性。
*   **统一存储层**：提供抽象的资产管理，支持自动将生成结果上传至 **本地存储**（开发环境）或 **S3/OSS 对象存储**（生产环境），并返回可访问的 URL。
*   **ComfyUI 集成**：原生内置对 ComfyUI 节点式工作流的支持，全生命周期管理从 Prompt 提交到图片/视频回调的过程。
*   **可扩展架构**：基于 **FastAPI**, **SQLAlchemy (Async)** 和 **Redis** 构建的解耦架构（摄入层、分发层、执行层分离）。

---

## 🛠️ 使用示例

### 提交任务
提交 `text-to-image` 任务并指定 provider。

```http
POST /task
Content-Type: application/json

{
  "task_type": "text-to-image",
  "params": {
    "provider": "comfyui",
    "prompt": "a futuristic cyberpunk city",
    "workflow": { ... }, 
    "server_address": "127.0.0.1:8188"
  }
}
```

### 响应
系统立即返回任务追踪 ID。

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Task queued"
}
```

### 获取结果
轮询或监听任务状态，获取生成资源的 URL。

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "images": [
      "http://api.genpulse.com/assets/550e8400.../result_0.png"
    ]
  }
}
```

---

## 📦 安装部署

1.  **克隆与安装**:
    ```bash
    git clone https://github.com/your-org/genpulse.git
    cd genpulse
    uv sync
    ```

2.  **配置环境**:
    创建 `.env` 文件:
    ```ini
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/genpulse
    REDIS_URL=redis://localhost:6379/0
    STORAGE_TYPE=local # 或 s3
    ```

3.  **启动服务**:
    ```bash
    # 一键启动 API 和 Worker (开发模式)
    uv run genpulse dev

    # 或者分别启动
    uv run genpulse api
    uv run genpulse worker
    ```

---

## 👨‍💻 开发

为了保证系统稳定性，我们遵循 **Dev（开发） -> Test（测试） -> Main（生产）** 的分支管理策略。
详细贡献指南请参考内部开发文档。
