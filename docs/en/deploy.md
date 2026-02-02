# Deployment Guide

This guide covers how to deploy GenPulse in a production environment using Docker Compose.

## Prerequisites
*   Docker & Docker Compose installed.
*   A Postgres database (optional, can be spun up via Compose).
*   A Redis instance (optional, can be spun up via Compose).

## 1. Quick Deploy
The provided `docker-compose.yml` includes the full stack:
*   **Web API**: Exposed on port 8000.
*   **Worker**: Background task processor.
*   **Monitor**: Celery Flower on port 5555.
*   **Redis & Postgres**: Persistence layer.

```bash
docker-compose up -d
```

## 2. Configuration Reference

GenPulse uses **Dynaconf**. You can override any setting using environment variables with the `GENPULSE_` prefix. Nested configs use double underscores `__`.

### Database & Queue
| Variable | Description |
|----------|-------------|
| `GENPULSE_DATABASE_URL` | SQLAlchemy Async Database URL. |
| `GENPULSE_REDIS__URL` | Redis URL for Celery Broker & Result Backend. |

### Object Storage (S3 / OSS / MinIO)
By default, GenPulse uses local disk storage. To switch to S3-compatible storage:

1. Set `GENPULSE_STORAGE__TYPE` to `s3` (or `oss`).
2. Configure credentials:

```bash
export GENPULSE_STORAGE__TYPE="s3"
export GENPULSE_STORAGE__S3_ENDPOINT_URL="https://s3.amazonaws.com" # or OSS endpoint
export GENPULSE_STORAGE__S3_REGION_NAME="us-east-1"
export GENPULSE_STORAGE__S3_BUCKET_NAME="my-genpulse-bucket"
export GENPULSE_STORAGE__S3_ACCESS_KEY="AK..."
export GENPULSE_STORAGE__S3_SECRET_KEY="SK..."
```

### ComfyUI Connectivity
The worker needs to access your ComfyUI instance via HTTP and WebSocket.

If ComfyUI is running on the **Host Machine**:
*   Ensure `extra_hosts` is configured in docker-compose (default is set).
*   Set `GENPULSE_PROVIDERS__COMFY_URL` to `http://host.docker.internal:8188`.

If ComfyUI is running in **another container**:
*   Ensure both containers are on the same Docker Network.
*   Set URL to `http://container_name:8188`.

## 3. Monitoring & Administration

### Admin Dashboard (SQLAdmin)
Access at `http://your-domain:8000/admin`.
Use this to view task history, inspect raw JSON params, and debug failures.

### Celery Flower
Access at `http://your-domain:5555`.
Use this to monitor worker load, view active tasks, and retry failed tasks.

### Health Checks
*   Liveness: `GET /health`
*   Deep Readiness (DB+Redis+Workers): `GET /health?full=true`
