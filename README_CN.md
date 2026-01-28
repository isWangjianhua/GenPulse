# GenPulse

> **高并发生成式 AI 后端系统**
>
> 🇺🇸 [English Documentation](./README.md)

GenPulse 是一个稳健的后端系统，专为大规模编排复杂的生成式 AI 工作流（图像、视频、音频）而设计。它为 AI 应用提供了可靠的任务调度、实时状态追踪以及统一的资产管理能力，现已支持 **7+ 主流云服务商**。

---

## 🚀 核心功能

*   **多模态融合**：统一的 **文生图**、**文生视频**、**图生视频** 接口，抹平不同供应商的参数差异。
*   **广泛的供应商支持**：开箱即用支持 **火山引擎 (VolcEngine)**、**腾讯云 (Tencent)**、**百度智能云 (Baidu)**、**可灵 AI (Kling)**、**Minimax**、**阿里云灵积 (DashScope)** 以及 **ComfyUI**。
*   **任务编排**：利用 **Celery** 分布式队列高效管理长耗时的 AI 生成任务。
*   **可靠的状态追踪**：采用“双重同步”机制——通过 MQ Pub/Sub 实现毫秒级更新，同时通过 PostgreSQL 保证数据的持久化与可审计性。
*   **统一存储层**：提供抽象的资产管理，支持自动将生成结果上传至 **本地存储**（开发环境）或 **S3/OSS 对象存储**（生产环境），并返回可访问的 URL。
*   **可扩展架构**：基于 **FastAPI**, **SQLAlchemy (Async)** 和 **Redis** 构建的解耦架构（摄入层、分发层、执行层分离）。

---

## 🧩 支持的供应商 (Providers)

| 供应商 | ID | 能力支持 |
| :--- | :--- | :--- |
| **火山引擎** | `volcengine` | 图片生成, 视频生成 |
| **腾讯云** | `tencent` | 图片生成 (混元), 视频生成 |
| **百度智能云** | `baidu` | 文生视频, 图生视频 |
| **可灵 AI** | `kling` | 高质量视频生成 |
| **Minimax** | `minimax` | 视频生成, 语音合成 |
| **灵积 DashScope** | `dashscope` | 图片生成 (Wanx), 视频生成 |
| **ComfyUI** | `comfyui` | 自定义节点工作流 |
| **Diffusers** | `diffusers` | 本地模型推理 |

---

## 🛠️ 使用示例

### 提交视频生成任务
指定 `text-to-video` 类型和供应商（例如 `kling`）。

```http
POST /task
Content-Type: application/json

{
  "task_type": "text-to-video",
  "params": {
    "provider": "kling",
    "prompt": "夕阳下的未来赛博朋克城市，无人机穿梭，电影质感",
    "model_name": "kling-v1"
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
    "video_url": "https://api.genpulse.com/assets/2026/01/24/result.mp4",
    "cover_url": "https://api.genpulse.com/assets/2026/01/24/cover.jpg"
  }
}
```

---

## 📦 安装部署

1.  **克隆与安装**:
    ```bash
    git clone https://github.com/your-org/genpulse.git
    cd genpulse
    ```

2.  **启动基础设施** (Docker):
    ```bash
    docker-compose up -d
    ```

3.  **安装依赖**:
    ```bash
    uv sync
    ```

4.  **配置环境**:
    复制 `.env.example` 创建 `.env`:
    ```ini
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/genpulse
    REDIS_URL=redis://localhost:6379/0
    
    # 填入需要的供应商 Key
    VOLC_ACCESS_KEY=...
    KLING_AK=...
    ```

5.  **启动服务**:
    ```bash
    # 一键启动 API 和 Worker (开发模式)
    uv run genpulse dev
    ```

---

## 👨‍💻 开发

为了保证系统稳定性，我们遵循 **Dev（开发） -> Test（测试） -> Main（生产）** 的分支管理策略。
详细贡献指南和代码规范请务必阅读 [AGENTS.md](./AGENTS.md)。
