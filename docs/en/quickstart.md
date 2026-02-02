# GenPulse Quick Start Guide

## 🚀 Launch Services

### Method 1: Development Mode (Recommended)
```bash
cd /path/to/GenPulse
uv run genpulse dev
```
Automatically starts:
- API Server: http://localhost:8000
- Celery Worker: Background process
- Flower Monitor: http://localhost:5555

### Method 2: Split Execution
```bash
# Terminal 1: API
uv run genpulse api

# Terminal 2: Worker
uv run genpulse worker

# Terminal 3: Flower
uv run genpulse monitor
```

### Method 3: Docker Compose
```bash
docker-compose up -d
```

## 📊 Dashboards

After launch, access:

### 1. API Documentation (Swagger UI)
**URL**: http://localhost:8000/docs

**Features**:
- 📖 View all endpoints
- 🧪 Test APIs online
- 📝 View Polymorphic Schemas
- 📤 Test File Uploads

### 2. Admin Dashboard (SQLAdmin)
**URL**: http://localhost:8000/admin

**Features**:
- 📋 Task History & Parameter Inspection
- 🗑️ Management actions

### 3. Flower Monitor
**URL**: http://localhost:5555

**Features**:
- 👷 Worker Health Status
- 📊 Real-time Task Metrics

## 📝 Examples: Creating Tasks

### 1. Text-to-Video (VolcEngine)
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "text-to-video",
    "provider": "volcengine",
    "params": {
      "model": "doubao-vid-1.0",
      "prompt": "A majestic lion walking in the savanna",
      "width": 1280,
      "height": 720
    }
  }'
```

### 2. ComfyUI Text-to-Image (Generic Template)
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "text-to-image",
    "provider": "comfyui",
    "params": {
      "model": "sdxl",
      "prompt": "Cyberpunk city at night",
      "width": 1024,
      "height": 1024
    }
  }'
```

### 3. Image-to-Video (Upload First)
```bash
# Step 1: Upload Image
curl -X POST http://localhost:8000/storage/upload \
  -F "file=@/path/to/image.png"

# Returns: {"url": "http://...", "key": "uploads/uuid.png"}

# Step 2: Create I2V Task (Minimax)
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "image-to-video",
    "provider": "minimax",
    "params": {
      "prompt": "Make it move",
      "first_frame_image": "http://..."
    }
  }'
```

## 🛠️ Troubleshooting

### Service Won't Start
```bash
# Check port conflicts
lsof -i :8000
lsof -i :5555

# Check Redis
redis-cli ping

# Debug Logs
uv run genpulse api --log-level debug
```

### Worker Not Processing
```bash
# Check Deep Health
curl http://localhost:8000/health?full=true
```
