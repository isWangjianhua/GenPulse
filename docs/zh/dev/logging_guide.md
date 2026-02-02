# 日志与调试

GenPulse 使用基于 **Loguru** 的集中式日志系统。这提供了结构化、彩色和自动轮换的日志。

## 1. 日志位置

- **控制台**: 默认情况下，日志会以彩色格式打印到 `stderr`。
- **文件**: 
    - `logs/genpulse.log`: 包含所有日志 (INFO 及以上)。每 500MB 轮换一次，保留 10 天。
    - `logs/error.log`: 仅包含 ERROR/CRITICAL 日志。

## 2. 阅读日志

格式: `Time | Level | Module:Function:Line - Message`

**示例:**
```text
2026-01-20 10:00:05.123 | INFO     | genpulse.worker:process_task:62 - Processing task task_123 (text-to-image)
2026-01-20 10:00:05.456 | ERROR    | genpulse.engines.comfy_engine:execute:56 - ComfyUI execution failed: Connection Refused
```

## 3. 调试策略

### 3.1 通过 Task ID 追踪执行
从 API 响应中复制 `task_id` 并在日志中 `grep` 它：

```bash
grep "task_123" logs/genpulse.log
```

这将显示该请求在 API 和 Worker 中的整个生命周期。

### 3.2 调整日志级别

要查看调试消息（包括变量值和 Mock 细节），请更改 `config/config.yaml` 中的级别：

```yaml
LOGGING:
  level: "DEBUG"
```

### 3.3 常见错误

| 错误 | 可能原因 | 修复 |
| :--- | :--- | :--- |
| `EngineError: Handler not found` | JSON 中的 `task_type` 与 `@registry.register` 不匹配 | 检查 `handlers.py` 装饰器中的拼写。 |
| `Boto3 missing` | 启用了 S3 存储但未安装 `boto3` | 运行 `uv add boto3`。 |
| `ConnectionRefusedError` | ComfyUI 未运行 | 手动启动 ComfyUI 或检查配置中的 `COMFY_URL`。 |
