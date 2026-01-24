# Tencent HTTP Polling Flow Implementation - Walkthrough

## 实现概述

本次实现完成了腾讯云 VOD AIGC 服务的完整 HTTP 请求轮询流程集成测试，包括：

1. **Video Handler 增强** - 为 `TextToVideoHandler` 添加了 Tencent provider 支持
2. **单元测试** - 创建了 handler 参数映射的单元测试
3. **集成测试** - 创建了端到端 HTTP 轮询流程测试

## 文件变更

### 1. 新增文件

#### `tests/integration/test_tencent_http_flow.py`
完整的端到端集成测试，包含：
- `test_tencent_text_to_image_http_polling_flow()` - 图像生成流程测试
- `test_tencent_text_to_video_http_polling_flow()` - 视频生成流程测试

测试流程：
```
HTTP POST /task → Redis MQ → Worker → Handler → TencentClient → 轮询 → GET /task/{id} → 验证结果
```

#### `tests/core/test_tencent_handlers.py`
Handler 参数映射的单元测试：
- `test_tencent_image_handler_parameter_mapping()` - 验证图像参数映射
- `test_tencent_video_handler_parameter_mapping()` - 验证视频参数映射
- `test_tencent_handler_error_handling()` - 验证错误处理

### 2. 修改文件

#### `src/genpulse/handlers/video.py`
添加了 Tencent provider 支持：

```python
def get_tencent_client():
    """获取 Tencent VOD 客户端"""
    from genpulse.clients.tencent.client import create_tencent_vod_client
    return create_tencent_vod_client()

# 在 TextToVideoHandler.execute() 中添加：
elif provider == "tencent":
    # 参数映射：通用参数 → TencentVideoParams
    tencent_params = TencentVideoParams(
        ModelName=params.get("model_name", "Hunyuan"),
        ModelVersion=params.get("model_version", "1.5"),
        Prompt=params.get("prompt"),
        NegativePrompt=params.get("negative_prompt"),
        OutputConfig={
            "AspectRatio": params.get("aspect_ratio", "16:9"),
            "Resolution": params.get("resolution", "720P")
        }
    )
    
    # 调用客户端并等待轮询完成
    response = await client.generate_video(tencent_params, wait=True)
    
    # 返回标准化结果
    return {
        "status": "succeeded",
        "result_url": response.result_url,
        "data": response.model_dump(),
        "provider": "tencent"
    }
```

## 测试验证

### 单元测试（已通过 ✓）

```bash
cd /home/mnze/projects/GenPulse/.wt/feature-tencent-http-flow
uv run pytest tests/core/test_tencent_handlers.py -v
```

**结果：** 3 passed ✓
- 图像参数映射测试 ✓
- 视频参数映射测试 ✓
- 错误处理测试 ✓

### 集成测试（需要真实凭证）

```bash
# 1. 设置环境变量
export TENCENTCLOUD_SECRET_ID="your_id"
export TENCENTCLOUD_SECRET_KEY="your_key"

# 2. 启动 Docker 服务
docker compose up -d

# 3. 运行集成测试
uv run pytest tests/integration/test_tencent_http_flow.py -v -s -m integration
```

**注意：** 集成测试需要：
- 真实的腾讯云 API 凭证
- 运行中的 Redis 和 PostgreSQL
- 网络连接到腾讯云 API

## 架构说明

### 完整请求流程

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /task
       │ {"task_type": "text-to-image", "provider": "tencent", ...}
       ▼
┌─────────────────┐
│  FastAPI Router │ (src/genpulse/routers/task.py)
└────────┬────────┘
         │ 1. 保存到 PostgreSQL
         │ 2. 推送到 Redis MQ
         ▼
┌─────────────┐
│  Redis MQ   │
└──────┬──────┘
       │ Worker 监听队列
       ▼
┌─────────────────┐
│     Worker      │ (src/genpulse/worker.py)
└────────┬────────┘
         │ 根据 task_type 路由
         ▼
┌──────────────────────┐
│ TextToImageHandler   │ (src/genpulse/handlers/image.py)
└──────────┬───────────┘
           │ provider == "tencent"
           ▼
┌──────────────────────┐
│  TencentVodClient    │ (src/genpulse/clients/tencent/client.py)
└──────────┬───────────┘
           │ 1. CreateAigcImageTask
           │ 2. 轮询 DescribeTaskDetail
           │ 3. 返回 result_url
           ▼
┌─────────────────┐
│  Worker 更新状态 │
└────────┬────────┘
         │ 更新 Redis + PostgreSQL
         ▼
┌─────────────┐
│   Client    │ GET /task/{id}
└─────────────┘ 获取最终结果
```

### 参数映射

**通用参数** (TaskRequest.params):
```json
{
  "model": "Hunyuan",
  "prompt": "A beautiful landscape",
  "aspect_ratio": "16:9",
  "resolution": "1024x576"
}
```

**Tencent 特定参数** (TencentImageParams):
```python
TencentImageParams(
    ModelName="Hunyuan",
    ModelVersion="3.0",
    Prompt="A beautiful landscape",
    OutputConfig={
        "AspectRatio": "16:9",
        "Resolution": "1024x576"
    }
)
```

## 下一步

1. **运行集成测试** - 需要用户提供腾讯云凭证
2. **合并到主分支** - 测试通过后合并到 `main`
3. **文档更新** - 更新 API 文档说明 Tencent provider 的使用方法

## 开发规范遵循

✓ 使用 Git Worktree 在 `.wt/` 下开发  
✓ 创建实现计划 `docs/plans/2026-01-24-tencent-http-polling-flow-test.md`  
✓ 遵循 TDD：先写测试，再实现功能  
✓ 使用 `uv` 作为包管理器  
✓ 遵循项目的分层架构：Router → Worker → Handler → Client
