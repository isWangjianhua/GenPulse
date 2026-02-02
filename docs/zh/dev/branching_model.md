# 分支与环境模型

为了确保稳定性和从开发到生产的清晰路径，GenPulse 遵循严格的分支和环境策略。

## 1. 分支策略

| 分支 | 目的 | 稳定性 | 目标环境 |
| :--- | :--- | :--- | :--- |
| **`main`** | 生产发布 | 最高 (Verifed tags) | 生产环境 (Production) |
| **`test`** | 预发布测试 | 高 (Release candidates) | 测试环境 (QA) |
| **`dev`** | 活跃开发 | 中 (Feature-complete) | 开发环境 (Sandbox) |
| **`feature/*`** | 新功能 | 低 (开发中) | 本地开发 |
| **`fix/*`** | Bug 修复 | 低 (开发中) | 本地开发 |

### 工作流:
1.  开发者从 `dev` 创建 `feature/xyz`。
2.  完成后，创建 PR 合并回 `dev`。
3.  定期将 `dev` 合并到 `test` 进行全面测试。
4.  验证通过后，将 `test` 合并到 `main` 并打标签 (例如 `v1.0.0`)。

## 2. 环境配置

环境通过 `ENV` 变量和 `.env` 文件控制。

| Env | `ENV` 值 | Redis Key 前缀 | DB 模式 | 本地库 |
| :--- | :--- | :--- | :--- | :--- |
| **Local** | `dev` | `dev:` | Local/Docker | 自动启动 (`genpulse dev`) |
| **Testing** | `test` | `test:` | 共享测试 DB | 独立 Service |
| **Prod** | `main` | `prod:` | 生产集群 | 独立集群 |

## 3. 配置管理

GenPulse 使用 **Dynaconf** 进行专业的分层配置管理。

### A. `.env` (环境特定 & 机密)
- **前缀**: 核心应用配置变量必须以 `GENPULSE_` 开头 (例如 `GENPULSE_REDIS__URL`) 以覆盖 Dynaconf 设置。
- **第三方凭证**: 某些 SDK 或提供商凭证可能遵循其特定的命名约定（如 `TENCENTCLOUD_SECRET_ID`, `KLING_AK`），不强制要求前缀。
- **环境切换**: 使用 `ENV_FOR_DYNACONF` (选项: `development`, `testing`, `production`)。
- **Git**: 永不提交。通过 `.env.example` 管理。

### B. `config.yaml` (分层默认值)
- **Sections**: 使用 `default`, `development`, `production` 头部。
- **Git**: 提交到代码库。
- **内容**: 非敏感的共享逻辑和回退值。

### C. 解析逻辑 & 验证
1. **验证**: 关键变量如 `DATABASE_URL` 在启动时使用 Dynaconf Validators 进行验证。
2. **合并**: 设置在各层之间合并: `config.yaml [default]` -> `config.yaml [env]` -> `.env` -> `Environment Variables`.

```python
# genpulse/config.py
from dynaconf import Dynaconf
settings = Dynaconf(envvar_prefix="GENPULSE", settings_files=["config/config.yaml"])
```
