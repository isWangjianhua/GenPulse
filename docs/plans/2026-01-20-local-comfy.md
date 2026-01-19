# Local ComfyUI Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Integrate a local ComfyUI instance managed by `comfy-cli`, configured to use CPU mode and project-level model storage.

**Architecture:**
- **Manager**: `comfy-cli` (installed via pip).
- **Runtime**: `libs/comfyui` (managed instance).
- **Models**: `models/` (project root, gitignored).
- **Config**: `core/comfy_manager.py` (GenPulse wrapper).

---

### Task 1: Environment & Dependency Setup

**Step 1: Add Dependencies**
- Add `comfy-cli` to `pyproject.toml`.
- Update `.gitignore` to exclude `models/` and `libs/comfyui/`.

**Step 2: Create Model Directory Structure**
- Create `models/checkpoints`, `models/loras`, etc.

---

### Task 2: ComfyUI Installation & Configuration

**Step 1: Install ComfyUI**
- Use `comfy --workspace libs/comfyui install` command (via python subprocess or manual run).
- Ensure CPU mode flags are ready.

**Step 2: Configure Model Paths**
- Create `extra_model_paths.yaml` in `libs/comfyui/`.
- Point `base_path` to `../../models` (relative to `libs/comfyui`).

---

### Task 3: Process Manager Implementation

**Files:**
- Create: `core/process_manager.py`

**Step 1: Implement `ComfyProcessManager`**
- `install()`: Run `comfy install`.
- `start()`: Run `comfy launch --cpu --port 8188`.
- `stop()`: Kill the subprocess.
- `is_running()`: Check health.

---

### Task 4: Integration with Worker

**Files:**
- Modify: `core/worker.py` or `manager.py (CLI)`

**Step 1: Auto-start Logic**
- Add a flag `--with-comfy` to the worker start command.
- If true, initialize `ComfyProcessManager` and start it in the background.

---

### Task 5: Verification

**Step 1: End-to-End Test**
- Start GenPulse with ComfyUI.
- Submit a task (simple workflow).
- Verify execution success on CPU.
