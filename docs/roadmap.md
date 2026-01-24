# Future Roadmap

This document outlines the strategic direction for GenPulse's development.

## Phase 1: Foundation & Connectivity (Completed)
- [x] Basic Async Architecture (FastAPI + Redis + Postgres)
- [x] Robust Logging & Error Handling
- [x] Local Diffusers Engine (Mock Mode)
- [x] **Multi-Provider Support**: 7+ Cloud Providers integrated (Volc, Tencent, Baidu, Kling, Minimax, DashScope).
- [x] **Client Abstraction Layer**: `BaseClient` with unified polling and error handling.
- [x] **MQ Abstraction Layer**: `BaseMQ` and `RedisMQ` implementation.
- [x] **Standardized Schemas**: Pydantic models for all external API interactions.

## Phase 2: Orchestration & Robustness (Current Focus)
### 1. Advanced Message Queueing
- [ ] **RabbitMQ Support**: Implement `RabbitMQ` adapter for `BaseMQ`.
- [ ] **Celery Integration**: Support Celery as an alternative worker runtime.
- [ ] **Message Reliability**: Implement Dead Letter Queues (DLQ) and retry policies.
- [ ] **Flow Control**: Rate limiting per provider to avoid API throttling.

### 2. API Generation & SDK
- [ ] **OpenAPI Spec**: Auto-generate complete OpenAPI/Swagger documentation.
- [ ] **Client SDK Generator**: Use `openapi-generator` to build Python/JS SDKs for GenPulse consumers.

### 3. Video Capability Expansion
- [ ] Unified `VideoHandler` capable of complex workflows (e.g., upscaling).
- [ ] "Image-to-Video" automatic adapter pipelines.

## Phase 3: User Experience (Next Up)
### 1. Web Dashboard (High Priority)
A visual interface to monitor the system in real-time.
- **Features**:
    - Live Task Queue visualization.
    - Asset Gallery.
    - System Health metrics.

## Phase 4: Enterprise Features (Q4 2026)
- [ ] **Multi-Tenant Support**: API Key management per user.
- [ ] **Billing System**: Credit deduction model.
- [ ] **Cluster Mode**: Horizontal scaling of Workers across multiple machines.
