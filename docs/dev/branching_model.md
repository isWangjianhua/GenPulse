# Branching & Environment Model

To ensure stability and a clear path from development to production, GenPulse follows a strict branching and environment strategy.

## 1. Branching Strategy

| Branch | Purpose | Stability | Target Environment |
| :--- | :--- | :--- | :--- |
| **`main`** | Production release | Highest (Verified tags) | Production |
| **`test`** | Pre-release testing | High (Release candidates) | Testing / QA |
| **`dev`** | Active development | Medium (Feature-complete) | Development / Sandbox |
| **`feature/*`** | New features | Low (In progress) | Local Dev |
| **`fix/*`** | Bug fixes | Low (In progress) | Local Dev |

### Workflow:
1.  Developers create `feature/xyz` from `dev`.
2.  Once complete, a PR is created to merge into `dev`.
3.  Periodically, `dev` is merged into `test` for comprehensive testing.
4.  Once verified, `test` is merged into `main` and tagged (e.g., `v1.0.0`).

## 2. Environment Configuration

Environments are controlled via `ENV` variable and `.env` files.

| Env | `ENV` Value | Redis Key Prefix | DB Mode | Local Libs |
| :--- | :--- | :--- | :--- | :--- |
| **Local** | `dev` | `dev:` | Local/Docker | Auto-spawn (`genpulse dev`) |
| **Testing** | `test` | `test:` | Shared Test DB | Dedicated Service |
| **Prod** | `main` | `prod:` | Production Cluster | Dedicated Cluster |

## 3. Configuration Management

We use `pydantic-settings` to manage configurations across environments.

```python
# genpulse/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = "dev"
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/genpulse"
    
    class Config:
        env_file = ".env"
```
