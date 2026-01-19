# Storage Layer & ComfyUI Handler Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Implement a unified storage abstraction (Local + S3 support) and the first real ComfyUI Handler to enable a full end-to-end AI generation workflow.

**Architecture:**
- **StorageProvider (Interface)**: Abstract base class for file operations.
- **LocalStorageProvider**: Current default implementation for local disk.
- **S3StorageProvider**: Pre-integrated implementation using `boto3`.
- **ComfyUIHandler**: The first execution agent specialized in local/remote ComfyUI orchestration.

---

### Task 1: Storage Abstraction Layer

**Files:**
- Create: `core/storage.py`
- Modify: `core/config.py` (Add storage settings)

**Step 1: Define Base Storage Interface**
Include methods: `upload_file`, `get_url`, `delete_file`.

**Step 2: Implement Local Storage**
Save files to `data/assets/` and generate local URL (e.g., `/static/assets/...`).

**Step 3: Implement S3-Compatible Storage**
Use `boto3` to support AWS and Aliyun OSS.

---

### Task 2: Gateway Static File Support

**Files:**
- Modify: `core/gateway.py`

**Step 1: Mount Static Files**
Mount the `data/assets/` directory so generated files can be accessed via HTTP during development.

---

### Task 3: ComfyUI Adapter & Handler

**Files:**
- Create: `core/comfy_client.py` (Low-level WS/HTTP client for ComfyUI)
- Create: `handlers/comfy_handler.py` (The High-level Agent)

**Step 1: Build ComfyUI Client**
Handle WebSocket connection, prompt queuing, and image retrieval from ComfyUI output.

**Step 2: Implement ComfyHandler**
- `validate_params`: Check for workflows and prompts.
- `execute`: Send to ComfyUI -> Wait for result -> Upload via Storage Agent -> Return Result.

---

### Task 4: Integration Test (End-to-End)

**Files:**
- Create: `tests/integration/test_comfy_workflow.py`

**Step 1: Mock ComfyUI environment** (or use a real local one if available).
**Step 2: Verify Workflow**: 
1. `POST /task` (Gateway persists to DB and mocks MQ)
2. `Worker` (Pops task, calls ComfyHandler)
3. `ComfyHandler` (Mocks execution, uploads to LocalStorage)
4. `Check DB`: Task status should be `completed` with a valid URL.

---

### Task 5: Documentation & Review

**Step 1: Update API Documentation**
Document how to use the ComfyUI task type.

**Step 2: Use requesting-code-review skill**
Review according to AGENTS.md.
