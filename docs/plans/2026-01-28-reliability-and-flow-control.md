---
title: Reliability and Flow Control Implementation Plan
status: draft
date: 2026-01-28
author: Antigravity
---

# Reliability and Flow Control Implementation Plan

## 1. Objective

Enhance the robustness of GenPulse by implementing mechanisms to handle task failures gracefully (Dead Letter Queues), ensure message delivery reliability (Retries), and protect downstream providers from being overwhelmed (Rate Limiting).

## 2. Context

Currently, GenPulse has basic task processing capability but lacks advanced safeguards:
- Failed tasks are simply marked as "FAILED" without clear retry policies.
- There is no specialized queue for inspecting problematic messages (DLQ).
- Worker blasts requests to external APIs (Tencent, Volc) as fast as possible, risking rate limits/throttling.

## 3. Proposed Changes

### 3.1 Dead Letter Queue (DLQ) Support
- **RabbitMQ**: Configure a `dlx` (Dead Letter Exchange) and `dlq` (Dead Letter Queue). Tasks that fail `N` times or are rejected will be routed here.
- **Celery**: Configure `task_reject_on_worker_lost` and routing for failed tasks.
- **Schema**: No schema changes needed, but `TaskProcessor` needs to handle "Reject" vs "Ack" signals.

### 3.2 Retry Strategy
- Implement exponential backoff for transient errors (Network, 503s).
- Implement "Fail Fast" for permanent errors (400 Bad Request, Validation Error).
- **Configuration**:
  ```yaml
  reliability:
    max_retries: 3
    retry_backoff: 2  # seconds (exponential factor)
  ```

### 3.3 Rate Limiting (Flow Control)
- **Component**: Create a `RateLimiter` class using Redis (e.g., Token Bucket or simple Window).
- **Scope**: Per-provider (e.g., `tencent`, `volcengine`).
- **Integration**: `TaskProcessor` checks `RateLimiter.acquire(provider)` before calling the handler.
- **Config**:
  ```yaml
  ratelimits:
    tencent: "5/second"
    volcengine: "20/minute"
  ```

## 4. Implementation Steps

1.  **Rate Limiter Implementation** (Low Risk)
    - Create `src/genpulse/infra/rate_limiter.py`.
    - Implement Redis-based limiting (using Lua script for atomicity).
    - Add Unit Tests.

2.  **Task Processor Updates** (Medium Risk)
    - Modify `TaskProcessor.process` to integrate `RateLimiter`.
    - Add retry logic wrapper around handler execution.
    - If rate limit hit -> Re-queue task with delay (or sleep if using simple worker).

3.  **MQ Adapter Updates** (High Risk)
    - **RabbitMQ**: Update `rabbitmq_mq.py` to declare DLX/DLQ queues on startup.
    - **Celery**: Update `celery_app.py` configs.

4.  **Verification**
    - Verify DLQ receives failed messages.
    - Verify tasks spin/wait when rate limit is exceeded.

## 5. Dependencies
- Rate limiting will require `redis` (which we already have).

## 6. Testing Plan
- **Unit**: Mock Redis for RateLimiter tests.
- **Integration**: Spin up RabbitMQ containers to test DLQ routing.
