# GenPulse Agentic System & Collaboration Guide

GenPulse is not just a backend service, but an orchestrated ecosystem of specialized agents designed for high-concurrency generative AI tasks. This document defines the roles, protocols, and development standards for both **Runtime Agents** (System components) and **Developer AI Agents** (AI collaborators like Antigravity).

---

## 1. Runtime Agents (The System)

Each core component in GenPulse is treated as a specialized agent with a clear mission and autonomy.

### 1.1 Ingestion Agent (`core/gateway.py`)
- **Role**: Gatekeeper and Task Originator.
- **Mission**: Accept user requests via HTTP or direct MQ, perform schema validation, persist initial state to PostgreSQL, and dispatch tasks to the primary broker (Redis).
- **Autonomy**: High authority over data integrity; can reject tasks before they enter the system.

### 1.2 Orchestration Agent (`core/worker.py` & Registry)
- **Role**: Intelligent Task Dispatcher.
- **Mission**: Monitor the Redis queue, identify `task_type`, and dynamically instantiate the correct `Handler Agent`.
- **Autonomy**: Responsible for life-cycle management, error recovery, and status synchronization between memory (Redis) and persistence (DB).

### 1.3 Execution Agents (`handlers/*`)
- **Role**: Domain Experts (e.g., ComfyUI expert, Video expert).
- **Mission**: Perform the actual "heavy lifting." They interact with local engines (subprocess) or remote APIs.
- **Autonomy**: Total control over the execution logic within their domain. They MUST provide progress updates via the provided context.

---

## 2. Developer AI Agent (The Collaborator)

This section defines the rules for AI assistants (like Antigravity) working on this codebase.

### 2.1 Branching & Environment Protocol
We follow a strict **Dev -> Test -> Main** progression to ensure stability.

| Branch | Identity | Environment | Rule |
| :--- | :--- | :--- | :--- |
| **`dev`** | Work Branch | Local Dev | Starting point for all features. |
| **`test`** | QA Branch | Staging/UAT | For integration testing and PR review. |
| **`main`** | Release Branch| Production | Tagged releases only. No direct commits. |

### 2.2 Standard Workflow (The "Golden Loop")
When implementing a new feature, the AI Agent MUST follow these steps:

1.  **Isolation**: Create a `feature/*` branch from `dev` using **Git Worktrees** to prevent workspace pollution.
2.  **Planning**: Use the `writing-plans` skill to create a detailed, task-by-task implementation plan in `docs/plans/`.
3.  **TDD**: For every task, write a failing test first, then implement minimal code to pass.
4.  **Verification**: Run `uv run pytest` to ensure zero regressions.
5.  **Review**: Submit a PR-like summary and use the `requesting-code-review` skill for self-audit or human feedback.
6.  **Merge**: Merge into `dev` and delete the worktree/feature branch.

### 2.3 Coding Standards
- **Manager**: Always use `uv` for dependency management.
- **Architecture**: Stick to the **Registry Pattern**. Do not hardcode business logic in `core/`.
- **Persistence**: Every task status change MUST be "Double-Synced" (Redis for speed, DB for permanence).
- **Aesthetics**: UI-related components (if any) must follow high-premium design standards.

---

## 3. Communication Protocols

### 3.1 Task Schema (The Common Language)
All agents communicate using a unified JSON schema:
```json
{
  "task_id": "uuid-v4",
  "task_type": "string",
  "params": { ... },
  "priority": "normal|high",
  "status": "pending|processing|completed|failed"
}
```

### 3.2 State Sync Protocol
Runtime agents MUST use the `update_status` helper provided by the `Orchestration Agent` to ensure consistent state broadcast:
1.  **Redis SET/EX**: For real-time polling (1-hour TTL).
2.  **Redis PUB**: For live events.
3.  **DB UPDATE**: For long-term audit and billing.

---

*This document is the "Supreme Directive" for AI-Agent collaboration on GenPulse. Any deviation from these protocols must be justified.*
