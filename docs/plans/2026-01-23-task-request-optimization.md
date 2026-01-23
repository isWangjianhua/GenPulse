# Task Request Structure Optimization Plan

## Overview
Optimize the `TaskRequest` structure in `src/genpulse/routers/task.py` to support a more typed and extensible parameter schema (Kling, Volcengine, etc.).

## Objectives
1.  Define a robust `TaskParams` Pydantic model.
2.  Update `TaskRequest` to use typed params.
3.  Ensure backward compatibility or clear migration path for `create_task`.

## Implementation Steps

### 1. Schema Definition
- **File**: `src/genpulse/routers/task.py`
- **Change**: Introduce `TaskParams` class.
- **Fields**:
    - `model`: str (Required)
    - `prompt`: str (Optional)
    - `negative_prompt`: str (Optional)
    - `image_urls`: List[str] (Optional)
    - `width`, `height`, `aspect_ratio`, `duration`: Generation configs.
    - `extra`: Dict for provider-specific params.
- **Config**: Allow extra fields.

### 2. Router Update
- **File**: `src/genpulse/routers/task.py`
- **Change**: Update `TaskRequest.params` type from `Dict` to `TaskParams`.
- **Change**: Add `provider` field to `TaskRequest`.
- **Logic**: In `create_task`, ensure `req.params.model_dump()` is used when passing to DB/MQ to serialize the Pydantic model to a dict.

### 3. Verification
- Verify `create_task` accepts the new JSON structure.
- Verify data passed to DB and MQ is a valid dictionary.
