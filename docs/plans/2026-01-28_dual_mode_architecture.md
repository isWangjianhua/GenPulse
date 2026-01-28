# Plan: Formalizing Dual-Mode Architecture (HTTP + RPC)

## Context
We have evolved the GenPulse architecture to support a "Dual-Mode" operation:
1.  **Public HTTP API**: Standard `POST /task` + `GET /task/{id}` polling for web/mobile clients.
2.  **Internal RPC**: Direct `RedisMQ` (or `CeleryMQ`) connection using `send_task_wait()` for microservices and internal scripts that need synchronous-like behavior.

We have also transitioned the primary robust queue implementation to **Celery** (backed by Redis), enabling ACK mechanisms and reliability, while retaining the simple `RedisMQ` class as a lightweight interface/legacy option (or bridging it to use Celery under the hood).

## Goals
1.  **Document the Dual-Mode Topology**: Clearly explain how both modes coexist and share the same worker cluster.
2.  **Update Usage Guides**: Show developers how to use the new RPC capabilities.
3.  **Reflect Tech Stack Changes**: Official adoption of Celery as the worker runtime.

## Affected Files

### 1. `README.md`
- [ ] Add "Dual-Mode Architecture" to Core Features.
- [ ] Add a code example for "Internal RPC Call" in the Usage section.
- [ ] Update "Start Infrastructure" commands to include Celery worker commands.

### 2. `docs/architecture_design.md`
- [ ] Update System Topology Diagram (Mermaid) to show two entry points (HTTP Gateway & Direct RPC).
- [ ] Add section "3.5 Dual-Mode Ingestion" explaining the rationale and flow.
- [ ] Update technology stack to emphasize Celery over raw Redis lists for production.

### 3. `docs/roadmap.md`
- [ ] Mark "Celery Integration" as Completed.
- [ ] Consolidate "Message Queue" goals (Reliability achieved via Celery).
- [ ] Add "RPC SDK" to future plans.

### 4. `docs/dev/`
- [ ] Update `local_testing_guide.md`: Add a section on "Testing RPC Mode" using the `direct_mq_client.py` example pattern.

## Execution Strategy
I will update these documents sequentially to ensure consistency in terminology (e.g., referring to "RPC Mode" consistently).
