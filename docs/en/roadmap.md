# Future Roadmap

This document outlines the strategic direction for GenPulse's development.

## Phase 1: Foundation & Connectivity (Completed)
- [x] Basic Async Architecture (FastAPI + Redis + Postgres)
- [x] Robust Logging & Error Handling
- [x] Local Diffusers Engine
- [x] **Multi-Provider Support**: 7+ Cloud Providers integrated.
- [x] **Client Abstraction Layer**: `BaseClient`.
- [x] **MQ Abstraction Layer**: `Celery` Integration.
- [x] **Rate Limiting**: Distributed token bucket limiter.

## Phase 2: Orchestration & Robustness (Completed)
### 1. ComfyUI Deep Integration
- [x] **ComfyEngine**: Dedicated engine for WebSocket communication.
- [x] **Template System**: JSON-based workflow templates (`template_name`).
- [x] **High Performance**: `SaveImageWebsocket` binary capture.

### 2. Unified Handlers
- [x] **Generic Dispatchers**: `ImageHandler` and `VideoHandler` routing to correct Providers or Engines.
- [x] **Dual-Mode Support**: HTTP Polling + Direct RPC.
- [x] **Unified Storage**: S3/OSS auto-upload.

## Phase 3: Developer Experience (Current Focus)
### 1. Web Dashboard
A visual interface for users to try out generation capabilities.
- [ ] Next.js / React Frontend.
- [ ] Real-time progress bars.
- [ ] Asset Gallery.

### 2. SDK Generation
- [ ] **OpenAPI Spec**: Refine for SDK generation.
- [ ] **Client SDKs**: Python/TypeScript client libraries.

## Phase 4: Enterprise Features (Q4 2026)
- [ ] **Multi-Tenant Support**: API Key management per user.
- [ ] **Billing System**: Credit deduction model.
- [ ] **Cluster Mode**: Horizontal scaling of Workers across multiple machines.
