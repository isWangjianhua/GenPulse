# 本地测试与 Mock 模式

本指南说明如何在不需要昂贵的 GPU 或下载大量模型文件的情况下针对 GenPulse 进行开发。

## 1. 概念

GenPulse 引擎（如 `diffusers`）支持 **Mock 模式**。在此模式下，引擎模拟网络延迟和处理步骤，但生成的是合成的"假"图像（例如纯色块），而不是运行真正的神经网络。

这使得前端和 API 开发人员能够：
- 测试完整的任务生命周期 (Pending -> Processing -> Completed)。
- 验证和文件上传。
- 验证 WebSocket/MQ 事件流。

...所有这些都可以在标准的笔记本电脑上完成。

## 2. 使用 Mock 模式

向 API 提交任务时，只需将 `model_id` 设置为 `"mock"`。

### 示例 Payload

```json
POST /task
{
  "task_type": "text-to-image",
  "params": {
    "provider": "diffusers",
    "model_id": "mock",
    "prompt": "This text is ignored in mock mode"
  }
}
```

### 预期行为

1.  **状态更新**: 您将在大约 1-2 秒内收到进度更新 (10% -> 50% -> 90%)。
2.  **结果**: 最终结果将是一个有效的 URL，指向本地存储中的生成 PNG 文件 (`data/assets/...`)。

## 3. 运行开发环境

启动全栈进行本地测试：

```bash
# 1. 启动 Redis (必需)
docker run -d -p 6379:6379 redis

# 2. 启动 GenPulse 开发模式
uv run genpulse dev
```

您将在终端中看到来自 API Server 和 Worker 的日志。

## 4. 测试 RPC 模式 (微服务)

要测试类同步 RPC 能力（不通过 HTTP 直接 MQ 交互）：

1.  **确保 Worker 正在运行**: Celery worker 必须处于活动状态。
2.  **运行示例客户端**:
    ```bash
    # 此脚本绕过 API 直接与 Redis 对话
    uv run python examples/direct_mq_client.py "Test prompt from RPC"
    ```

3.  **结果**: 您应该看到脚本推送任务，等待（显示进度条），然后在 worker 完成作业后打印最终的 JSON 结果。
