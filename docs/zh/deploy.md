# 部署指南

本指南涵盖了如何使用 Docker Compose 在生产环境中部署 GenPulse。

## 前置条件
*   安装 Docker & Docker Compose。
*   PostgreSQL 数据库（可选，可通过 Compose 启动）。
*   Redis 实例（可选，可通过 Compose 启动）。

## 1. 快速部署
提供的 `docker-compose.yml` 包含了完整的技术栈：
*   **Web API**: 暴露在 8000 端口。
*   **Worker**: 后台任务处理器。
*   **Monitor**: 暴露在 5555 端口的 Celery Flower。
*   **Redis & Postgres**: 持久化层。

```bash
docker-compose up -d
```

## 2. 配置参考

GenPulse 使用 **Dynaconf**。您可以使用带有 `GENPULSE_` 前缀的环境变量覆盖任何设置。嵌套配置使用双下划线 `__`。

### 数据库 & 队列
| 变量 | 描述 |
|----------|-------------|
| `GENPULSE_DATABASE_URL` | SQLAlchemy 异步数据库 URL。 |
| `GENPULSE_REDIS__URL` | 用于 Celery Broker & Result Backend 的 Redis URL。 |

### 对象存储 (S3 / OSS / MinIO)
默认情况下，GenPulse 使用本地磁盘存储。要切换到兼容 S3 的存储：

1. 设置 `GENPULSE_STORAGE__TYPE` 为 `s3` (或 `oss`)。
2. 配置凭证：

```bash
export GENPULSE_STORAGE__TYPE="s3"
export GENPULSE_STORAGE__S3_ENDPOINT_URL="https://s3.amazonaws.com" # 或 OSS 端点
export GENPULSE_STORAGE__S3_REGION_NAME="us-east-1"
export GENPULSE_STORAGE__S3_BUCKET_NAME="my-genpulse-bucket"
export GENPULSE_STORAGE__S3_ACCESS_KEY="AK..."
export GENPULSE_STORAGE__S3_SECRET_KEY="SK..."
```

### ComfyUI 连接性
Worker 需要通过 HTTP 和 WebSocket 访问您的 ComfyUI 实例。

如果 ComfyUI 运行在 **宿主机** 上：
*   确保 `docker-compose` 中配置了 `extra_hosts` (默认已设置)。
*   设置 `GENPULSE_PROVIDERS__COMFY_URL` 为 `http://host.docker.internal:8188`。

如果 ComfyUI 运行在 **另一个容器** 中：
*   确保两个容器在同一个 Docker Network 上。
*   设置 URL 为 `http://容器名:8188`。

### 供应商凭证 (云 API)
要使用基于云的 AI 提供商，请设置相应的 API Key：

| 供应商 | 变量 |
|----------|----------|
| **VolcEngine (火山)** | `GENPULSE_PROVIDERS__VOLC_ACCESS_KEY`, `GENPULSE_PROVIDERS__VOLC_SECRET_KEY` |
| **Kling AI (可灵)** | `GENPULSE_PROVIDERS__KLING_ACCESS_KEY`, `GENPULSE_PROVIDERS__KLING_SECRET_KEY` |
| **Baidu (百度)** | `GENPULSE_PROVIDERS__BAIDU_ACCESS_KEY`, `GENPULSE_PROVIDERS__BAIDU_SECRET_KEY` |
| **Minimax** | `GENPULSE_PROVIDERS__MINIMAX_API_KEY`, `GENPULSE_PROVIDERS__MINIMAX_GROUP_ID` |
| **Tencent (腾讯)** | `GENPULSE_PROVIDERS__TENCENT_SECRET_ID`, `GENPULSE_PROVIDERS__TENCENT_SECRET_KEY` |
| **DashScope (阿里)** | `GENPULSE_PROVIDERS__DASHSCOPE_API_KEY` |

## 3. 监控管理

### Admin Dashboard (SQLAdmin)
访问地址：`http://your-domain:8000/admin`。
用于查看任务历史、检查原始 JSON 参数和调试失败任务。

### Celery Flower
访问地址：`http://your-domain:5555`。
用于监控 Worker 负载、查看活动任务和重试失败任务。

### 健康检查
*   存活检查: `GET /health`
*   深度就绪检查 (DB+Redis+Workers): `GET /health?full=true`
