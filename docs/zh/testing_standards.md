# GenPulse 测试标准

本文档概述了 GenPulse 项目的测试策略、结构和最佳实践。

## 1. 目录结构

我们首先按**范围 (scope)** 划分测试，然后按**模块 (module)** 划分。

```text
tests/
├── unit/                   # 快速: 无外部 I/O (无 DB, Network, Redis)
│   ├── clients/            # 提供商客户端的单元测试
│   ├── engines/            # AI 引擎的逻辑测试 (模拟运行时)
│   ├── handlers/           # 逻辑 Handle 的单元测试
│   └── infra/              # 核心基础设施逻辑
│
├── integration/            # 较慢: 使用本地依赖 (Docker DB/Redis)
│   ├── api/                # 使用 TestClient 测试 FastAPI 端点
│   ├── flows/              # 多组件流程 (如 Handler -> Engine)
│   └── infra/              # 与 Redis/RabbitMQ 的真实交互
│
├── external/               # 慢/昂贵: 与真实 API 交互 (Tencent/Volc)
│   └── ...                 # 需要配置 API Key。
│
├── conftest.py             # 全局 fixtures (event_loop, mock_redis)
└── pytest.ini              # 配置
```

## 2. 测试原则

### 2.1 测试金字塔
- **Unit (70%)**: 业务逻辑, 参数验证, 错误处理。必须在 <1秒 内运行完成。
- **Integration (20%)**: DB 查询, MQ 往返, 辅助工作流。
- **E2E/External (10%)**: 关键用户路径, 冒烟测试。

### 2.2 Asyncio 最佳实践
由于 GenPulse 是高度异步的：
- 使用 `@pytest.mark.asyncio`。
- **Fixtures 策略**: 异步 fixture 通常应为 `function` 作用域，以避免 "Event loop is closed" 错误。
  ```python
  @pytest.fixture
  async def async_client():
      async with AsyncClient(...) as client:
          yield client
  ```
- **超时**: 在测试中使用 `asyncio.wait_for` 以防止因 awaitable 损坏而导致永久挂起。

## 3. AI Mock 策略

测试 AI 系统非常独特，因为模型推理既慢又重。

### 3.1 权重模型
在单元或集成测试中 **决不 (NEVER)** 加载真实权重 (如 SDXL, LLMs)。
- **Mocking**: Patch 加载函数。
- **Dummy Outputs**: 返回小的随机字节或 1x1 像素图像作为生成结果。

```python
# GOOD
mock_pipeline.generate.return_value = [PIL.Image.new('RGB', (1, 1))]

# BAD
real_pipeline = StableDiffusionPipeline.from_pretrained(...) # 6GB download!
```

### 3.2 外部提供商
尽量使用 `respx` 或 `httpx_mock` 来模拟与腾讯/火山引擎的 HTTP 交互，除非是在编写 `external` 测试。

## 4. 代码风格与模式

### 4.1 AAA 模式
清晰地组织测试：
- **Arrange** (Given): 准备 fixtures, 数据。
- **Act** (When): 调用被测方法。
- **Assert** (Then): 验证结果。

### 4.2 优先使用 Fixtures 而非 Setup
优先使用 `pytest.fixture` 而不是 `unittest.TestCase.setUp`。这实现了依赖注入和更好的复用性。

### 4.3 快照测试 (可选)
对于大型 JSON 输出或复杂的字典，考虑使用 `syrupy`。
```python
def test_complex_output(snapshot):
    assert result == snapshot
```

## 5. 运行测试

```bash
# 运行所有 (Unit + Integration)
uv run pytest

# 仅运行 Unit (快速开发循环)
uv run pytest tests/unit

# 运行 External (需显式开启)
uv run pytest tests/external

# 失败时调试
uv run pytest -vv --pdb
```
