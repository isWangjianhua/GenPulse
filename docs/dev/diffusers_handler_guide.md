# Diffusers Handler Usage Guide

## Overview
The Diffusers Handler allows you to run Stable Diffusion and other models directly via the `diffusers` library. This is often faster and consumes less memory than heavy node-based systems like ComfyUI for standard generation tasks.

## Task Submission

### API Endpoint
```http
POST /task
Content-Type: application/json

{
  "task_type": "text-to-image",
  "params": {
    "provider": "diffusers",
    "model_id": "runwayml/stable-diffusion-v1-5",
    "prompt": "a futuristic cyberpunk city",
    "negative_prompt": "blurry, low quality",
    "steps": 25,
    "guidance_scale": 7.5,
    "seed": 42
  }
}
```

### Parameters

- **task_type**: Must be `text-to-image`.
- **provider**: Set to `diffusers`.
- **model_id** (optional): The Hugging Face model ID. Defaults to `runwayml/stable-diffusion-v1-5`.
- **prompt** (required): The primary text prompt.
- **negative_prompt** (optional): Negative prompt.
- **steps** (optional): Number of inference steps (default: 30).
- **guidance_scale** (optional): CFG scale (default: 7.5).
- **seed** (optional): Random seed for reproducibility.

## Performance Features

1. **Model Caching**: Models are loaded once and kept in memory for subsequent requests.
2. **Non-blocking Execution**: Inference runs in a separate thread to keep the worker responsive for progress updates.
3. **Real-time Progress**: Updates task progress to Redis and PostgreSQL during the diffusion process.
4. **Auto Device Detection**: Automatically uses CUDA if available, otherwise falls back to CPU.

## Examples

### Text to Image
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "text-to-image",
    "params": {
      "provider": "diffusers",
      "prompt": "a beautiful forest with sunlight filtering through leaves",
      "steps": 20
    }
  }'
```

## Setup Requirements

The system must have the following dependencies installed:
- `diffusers`
- `torch`
- `transformers`
- `accelerate`

These are managed via `uv`. Run `uv sync` to ensure your environment is ready.
