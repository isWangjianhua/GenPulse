# Optimization and Expansion Plan (Next Steps)
**Date:** 2026-01-28  
**Status:** Draft / Planned  
**Previous Phase:** Dual-Mode Architecture & Reliability (Completed)

## 1. Executive Summary (Current State)
GenPulse has successfully transitioned to a robust **Celery-Only Architecture**, supported by Redis as both the broker and result backend. The system now supports a unique **Dual-Mode** operation:
1.  **Public HTTP API**: Standard Async REST pattern (Submit -> ID -> Poll).
2.  **Internal RPC**: Microservice-friendly synchronous-like calls via `CeleryMQ.send_task_wait` (using Redis Pub/Sub).

Core reliability features (Rate Limiting, Retries, Exponential Backoff) are implemented. The next phase focuses on **Observability, Production Readiness (Storage), and Developer Experience**.

---

## 2. Priority 1: Observability & Monitoring
**Problem:** Currently, task visibility relies on logs or raw Redis inspection. We lack real-time insights into worker load, queue depth, and failure rates.

### Action Items
- [ ] **Integrate Celery Flower**
    - **Why:** Real-time web UI for monitoring workers and tasks.
    - **Implementation:**
        - Add `flower` dependency.
        - Add `genpulse monitor` CLI command to launch Flower.
        - Configure Flower to serve at `http://localhost:5555`.
        - Ensure it connects to the same Redis Broker.
- [ ] **Health Check Probes**
    - **Why:** Kubernetes/Docker lifecycles need to know if the worker is actually stuck.
    - **Implementation:** Update `/health` endpoint to perform a Celery `inspect().ping()` to verify worker responsiveness, not just Redis connectivity.

---

## 3. Priority 2: Unified Storage Layer (Production Ready)
**Problem:** `src/genpulse/infra/storage.py` currently defaults to local filesystem. For production (and multi-node clusters), generated assets (images/videos) MUST be stored in object storage (S3).

### Action Items
- [ ] **Refactor Storage Interface**
    - Create an abstract `StorageBackend` class.
    - Implement `LocalStorage` (Keep existing logic).
    - Implement `S3Storage` (using `boto3` or `minio`).
- [ ] **Configuration Switch**
    - Use `Dynaconf` to switch backends based on `env`:
      ```yaml
      STORAGE:
        TYPE: "s3" # or "local"
        BUCKET: "genpulse-assets"
        REGION: "us-east-1"
      ```
- [ ] **Presigned URLs**
    - Update the result dict to return pre-signed URLs (valid for 1 hour) instead of raw paths when using S3.

---

## 4. Priority 3: Deployment Engineering
**Problem:** Starting the system requires multiple terminal tabs (`uvicorn`, `celery`, `redis`, `db`).

### Action Items
- [ ] **Docker Compose**
    - Create `docker-compose.yml` defining services:
        - `redis`
        - `postgres`
        - `genpulse-api`
        - `genpulse-worker`
        - `genpulse-dashboard` (Flower)
- [ ] **Production Dockerfile**
    - Multi-stage build (build deps vs runtime).
    - Hardened security (non-root user).

---

## 5. Priority 4: API & SDK Enhancements
**Problem:** The API input schema is generic (`dict`). Frontend developers have to guess parameters for different providers (e.g., "Does VolcEngine use `prompt` or `text`?").

### Action Items
- [ ] **Strict Provider Schemas**
    - Define Pydantic models for each Provider's request body:
        - `VolcVideoParams`
        - `KlingImageParams`
    - Use `pydantic.Field(..., description="...")` to generate rich Swagger docs.
- [ ] **Dynamic Schema Endpoint**
    - Create `GET /meta/schemas/{provider}` to let frontends dynamically render forms based on the backend's capabilities.

---

## 6. Feature Expansion Ideas

### A. Deep ComfyUI Integration
Instead of just triggering workflows, allow GenPulse to **parse** them.
- **Workflow Analyzer**: Upload a `workflow_api.json`, and GenPulse identifies all primitive input nodes (`KSampler seed`, `CLIPTextEncode text`).
- **Auto-Form**: Automatically generate a UI or API Schema for that specific workflow.

### B. Image-to-Video Pipeline
- **Multipart Upload**: Add endpoints to upload an image first.
- **Asset ID**: Return an `asset_id` (stored in S3).
- **Pipeline**: Pass `asset_id` to the Celery worker, which downloads the image -> processes it -> uploads the result.

---

## 7. Known Tech Debt / Maintenance
- **Testing**: `tests/integration` needs to be expanded to cover actual Handler logic (mocking external API calls).
- **Java SDK**: The guide exists (`docs/dev/java_integration.md`), but publishing a small Maven package would be better.
