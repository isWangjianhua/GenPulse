# Diffusers Native Handler Implementation Plan

> **Goal:** Implement a native execution agent using the `diffusers` library to provide high-performance, predictable image generation without ComfyUI overhead.

## 1. Dependencies & Environment
- **Add Packages**: `diffusers`, `torch`, `transformers`, `accelerate`.
- **Optimization**: Use `float16` and `safetensors` by default.

## 2. Handler Design (`handlers/diffusers_handler.py`)
- **Task Type**: `diffusers_txt2img`.
- **Parameters**: 
  - `model_id`: e.g., "runwayml/stable-diffusion-v1-5".
  - `prompt`/`negative_prompt`.
  - `steps`, `guidance_scale`.
  - `seed`.
- **Optimization**: Implement a simple **Singleton Loader** or global cache for pipelines to avoid reloading models for every task.

## 3. Implementation Steps

### Task 1: Foundation
- Update `pyproject.toml` with necessary dependencies.
- Create `handlers/diffusers_handler.py` boilerplate.

### Task 2: Pipeline Management
- Implement a helper to load and cache pipelines in memory.
- Support CPU/GPU auto-detection.

### Task 3: Execution Logic
- Implement `execute` method:
  1. Parse parameters.
  2. Load/Get Pipeline.
  3. Run inference with progress callbacks (using `diffusers` callback system to feed our `update_status`).
  4. Collect results and save via `StorageProvider`.

### Task 4: Testing (TDD)
- **Unit Test**: Mock `StableDiffusionPipeline` to verify parameter passing and result handling.
- **Integration Test**: Verify the Worker invokes the correct handler for `task_type="diffusers_txt2img"`.

## 4. Documentation
- Add usage guide for Diffusers tasks.
