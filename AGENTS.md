# GenPulse Agentic System & Collaboration Guide

GenPulse is not just a backend service, but an orchestrated ecosystem of specialized agents designed for high-concurrency generative AI tasks. This document defines the roles, protocols, and development standards for both **Runtime Agents** (System components) and **Developer AI Agents** (AI collaborators like Antigravity).

---

## 1. Runtime Agents (The System)

Each core component in GenPulse is treated as a specialized agent with a clear mission and autonomy.

### 1.1 Ingestion Agent (`app.py` & `routers/*`)
- **Role**: Gatekeeper and Task Originator.
- **Mission**: Accept user requests via FastAPI, perform schema validation, persist initial state to PostgreSQL, and dispatch tasks to the primary broker (Redis).
- **Autonomy**: High authority over data integrity; can reject tasks before they enter the system.

### 1.2 Orchestration Agent (`worker.py`)
- **Role**: Intelligent Task Dispatcher.
- **Mission**: Monitor the Message Queue, identify `task_type`, and dynamically instantiate the correct `Feature Handler`.
- **Autonomy**: Responsible for life-cycle management, error recovery, and status synchronization between memory (Redis) and persistence (DB).

### 1.3 Execution Agents (`handlers/*` & `clients/*`)
- **Role**: Domain Experts and External Connectors.
- **Mission**: Perform the actual "heavy lifting." Feature handlers coordinate with specialized engines or external clients to generate content.
    - **Handlers**: Business logic layer (e.g., `TextToVideoHandler`).
    - **Clients**: Infrastructure layer connecting to external providers (e.g., `VolcEngineClient`, `TencentVodClient`).
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
- **Architecture**: Follow the `Handlers -> Clients -> Engines` layered model. Use `genpulse.handlers.registry` for task discovery.
- **MQ Abstraction**: Do NOT use raw Redis commands for queuing. Use `genpulse.infra.mq.get_mq()` to obtain the `BaseMQ` instance.
- **Persistence**: Every task status change MUST be "Double-Synced" (MQ cache for speed, PostgreSQL via DBManager for permanence).
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
1.  **MQ Cache (SET/EX)**: For real-time polling (1-hour TTL).
2.  **MQ Pub/Sub**: For live events.
3.  **DB UPDATE**: For long-term audit and billing.

---

## 4. Development Standards & Style Guide

### 4.1 Python Code Style
- **Standard**: Follow **PEP 8** strictly.
- **Formatter**: Code is usually formatted, but always prefer clarity.
- **Type Hints**: **MANDATORY** for all function signatures. Use `typing.Optional`, `typing.List`, etc., or standard collections in Python 3.9+.
    ```python
    def process_data(data: Dict[str, Any], retries: int = 3) -> Optional[str]: ...
    ```
- **Naming**:
    - Classes: `PascalCase` (e.g., `TextToImageHandler`)
    - Functions/Variables: `snake_case` (e.g., `generate_video`)
    - Constants: `UPPER_CASE` (e.g., `DEFAULT_TIMEOUT`)

### 4.2 Docstring Specification
Use **Google Style** docstrings for all public modules, classes, and methods.

```python
def connect(self, timeout: int = 30) -> bool:
    """
    Connects to the remote service using the engineered protocol.

    Args:
        timeout: The maximum time to wait for a connection in seconds.

    Returns:
        True if connection was successful, False otherwise.

    Raises:
        ConnectionError: If network is unreachable.
    """
```

### 4.3 Pydantic Schema Standards
All data entering or leaving the system boundary (API requests, Client responses) MUST be typed with Pydantic.

- **Description**: Every field MUST have a `description`.
- **Validation**: Use `Field` for validation rules (min/max/regex).
- **Config**: Use `model_config = ConfigDict(...)` for configuration (e.g., `populate_by_name`).

```python
class VideoParams(BaseModel):
    prompt: str = Field(..., description="The text prompt for video generation.", max_length=1000)
    duration: int = Field(5, description="Duration in seconds.", ge=1, le=10)
```

### 4.4 Client Development Standards
When adding a new provider (e.g., "DeepSeek"):

1.  **Inheritance**: Must inherit from `genpulse.clients.base.BaseClient`.
2.  **Factory**: Provide a `create_<provider>_client` factory function.
3.  **Async**: All I/O methods must be `async`.
4.  **Polling**: Use `self.poll_task(...)` for long-running operations. Do not implement custom loops effectively duplicating this logic.

### 4.5 Handler Development Standards
1.  **Inheritance**: Must inherit from `genpulse.handlers.base.BaseHandler`.
2.  **Registry**: Use `@registry.register("task-type")` decorator.
3.  **Context**: Always use `context.update_status(...)` for progress reporting. Never print to stdout.
4.  **Provider Routing**: Inspect `params.get("provider")` to route to the correct `Client` or `Engine`.

### 4.6 Error Handling
- **Exceptions**: Use custom exceptions (e.g., `EngineError`) rather than bare `Exception`.
- **Logging**: Use `loguru` (`from loguru import logger`).
- **Granularity**: Wrap external calls in `try/except` blocks to catch provider-specific errors and re-raise them with context.

### 4.7 Testing Standards
- **Framework**: `pytest`.
- **Location**: `tests/`.
- **Mocking**: Use `unittest.mock` or `pytest-mock` to mock external API calls. Never hit real paid APIs during unit tests.

*This document is the "Supreme Directive" for AI-Agent collaboration on GenPulse. Any deviation from these protocols must be justified.*
