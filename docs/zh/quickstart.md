# GenPulse 快速启动指南

## 🚀 启动服务

### 方式 1: 开发模式（推荐）
```bash
cd /path/to/GenPulse
uv run genpulse dev
```
这会自动启动：
- API Server: http://localhost:8000
- Celery Worker: 后台运行
- Flower Monitor: http://localhost:5555

### 方式 2: 分离启动
```bash
# 终端 1: API
uv run genpulse api

# 终端 2: Worker
uv run genpulse worker

# 终端 3: Flower
uv run genpulse monitor
```

### 方式 3: Docker Compose
```bash
docker-compose up -d
```

## 📊 访问看板

启动服务后，可以访问以下界面：

### 1. API 文档 (Swagger UI)
**URL**: http://localhost:8000/docs

**功能**：
- 📖 查看所有 API 接口
- 🧪 在线测试接口
- 📝 查看多态 Schema（ComfyUI、VolcEngine 等）
- 📤 测试文件上传

**主要接口**：
- `POST /task` - 创建任务（支持多种 provider）
- `GET /task/{task_id}` - 查询任务状态
- `POST /storage/upload` - 上传文件
- `GET /health` - 健康检查
- `GET /health?full=true` - 深度健康检查（包含 Worker 状态）

### 2. Admin Dashboard (SQLAdmin)
**URL**: http://localhost:8000/admin

**功能**：
- 📋 查看所有任务历史
- 🔍 搜索任务（按 ID、状态）
- 📊 查看任务详情（JSON 参数、结果）
- 🗑️ 删除失败任务
- 📈 任务统计

### 3. Flower Monitor (Celery 监控)
**URL**: http://localhost:5555

**功能**：
- 👷 查看 Worker 状态（在线/离线）
- 📊 实时任务监控
- 📈 任务执行统计
- 🔄 重试失败任务

## 📝 示例：创建任务

### 1. 文生视频 (火山引擎)
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "text-to-video",
    "provider": "volcengine",
    "params": {
      "model": "doubao-vid-1.0",
      "prompt": "一只威严的狮子漫步在草原上",
      "width": 1280,
      "height": 720
    }
  }'
```

### 2. ComfyUI 文生图 (通用模板模式)
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "text-to-image",
    "provider": "comfyui",
    "params": {
      "model": "sdxl",
      "prompt": "赛博朋克风格的城市夜景",
      "width": 1024,
      "height": 1024
    }
  }'
```

### 3. 图生视频 (先上传图片)
```bash
# 步骤 1: 上传图片
curl -X POST http://localhost:8000/storage/upload \
  -F "file=@/path/to/image.png"

# 返回: {"url": "http://...", "key": "uploads/uuid.png"}

# 步骤 2: 创建 I2V 任务 (Minimax)
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "image-to-video",
    "provider": "minimax",
    "params": {
      "prompt": "让画面动起来",
      "first_frame_image": "http://..."
    }
  }'
```

## 🛠️ 故障排查

### 服务无法启动
```bash
# 检查端口占用
lsof -i :8000
lsof -i :5555

# 检查 Redis
redis-cli ping

# 查看日志
uv run genpulse api --log-level debug
```

### Worker 不工作
```bash
# 检查 Worker 状态
curl http://localhost:8000/health?full=true
```
