# GenPulse

> **High-Concurrency Generative AI Backend System**

GenPulse is an agentic, event-driven backend system designed to orchestrate complex Generative AI workflows (Image, Video, Audio) at scale. It features a robust architecture separating ingestion, orchestration, and execution, ensuring high reliability and observability.

---

## 🚀 Key Features

*   **Agentic Architecture**: Components act as specialized agents (Ingestion, Orchestration, Execution) with high autonomy.
*   **Double-Sync State**: Real-time status updates via Redis (for speed) and persistent records via PostgreSQL (for audit/reliability).
*   **Unified Storage Layer**: Abstracted asset management supporting both **Local Storage** (development) and **S3/OSS** (production).
*   **Extensible Handlers**: Plugin-based execution agents. Currently supports **ComfyUI** for complex node-based image generation.
*   **Modern Stack**: Built with **FastAPI**, **Redis**, **SQLAlchemy (Async)**, and managed via **uv**.

---

## 🏗️ Architecture

The system follows a strict separation of concerns, defined in [AGENTS.md](./AGENTS.md):

1.  **Ingestion Agent** (`Gateway`): Validates requests and persists initial state.
2.  **Orchestration Agent** (`Worker`): Polls queues and dispatches tasks to domain experts.
3.  **Execution Agents** (`Handlers`): Specialized logic (e.g., ComfyHandler) that interacts with AI engines.

![Architecture Flow](https://via.placeholder.com/800x400?text=Ingestion+->+MQ+->+Orchestrator+->+ComfyUI+->+Storage)

---

## 🛠️ Getting Started

### Prerequisites

*   **Python 3.12+**
*   **uv** (Python package manager)
*   **PostgreSQL** (Database)
*   **Redis** (Message Broker)
*   *(Optional)* **ComfyUI** instance (for image generation tasks)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/genpulse.git
    cd genpulse
    ```

2.  **Install dependencies**:
    ```bash
    uv sync
    ```

3.  **Configure Environment**:
    Create a `.env` file based on your needs:

    ```ini
    ENV=dev
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/genpulse
    REDIS_URL=redis://localhost:6379/0
    
    # Storage (Options: local, s3)
    STORAGE_TYPE=local
    STORAGE_LOCAL_PATH=data/assets
    
    # S3 (Optional)
    # S3_ENDPOINT_URL=https://s3.amazonaws.com
    # S3_ACCESS_KEY=xxx
    # S3_SECRET_KEY=xxx
    # S3_BUCKET_NAME=genpulse
    ```

4.  **Initialize Database**:
    ```bash
    # Ensure Postgres is running first
    uv run alembic upgrade head
    ```

### Running the System

You can run components individually or via the manager (coming soon).

**1. Start the Gateway (API)**
```bash
uv run uvicorn core.gateway:app --reload
```

**2. Start the Worker (Orchestrator)**
```bash
uv run python -m core.worker
```

---

## 💡 Usage

### Submitting a ComfyUI Task

GENPULSE allows you to execute ComfyUI workflows and get back a managed URL for the result.

**Request:**
```http
POST /task
Content-Type: application/json

{
  "task_type": "comfyui",
  "params": {
    "server_address": "127.0.0.1:8188",
    "workflow": { ... } // ComfyUI API JSON
  }
}
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Task received and queued"
}
```

**Polling Status:**
```http
GET /task/550e8400-e29b-41d4-a716-446655440000
```

---

## 👨‍💻 Development

We follow a strict **Dev -> Test -> Main** workflow.

-   **`dev`**: Main development branch.
-   **`test`**: Integration testing / Staging.
-   **`main`**: Production releases.

**Running Tests**:
```bash
uv run pytest
```

For more details on roles and protocols, please read **[AGENTS.md](./AGENTS.md)**.
