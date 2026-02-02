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

GenPulse uses **Dynaconf** for a professional, layered configuration management system.

### A. `.env` (Environment-Specific & Secrets)
- **Prefix**: All variables must start with `GENPULSE_` (e.g., `GENPULSE_REDIS__URL`).
- **Environment Switcher**: Use `ENV_FOR_DYNACONF` (options: `development`, `testing`, `production`).
- **Git**: Never committed. Manage via `.env.example`.

### B. `config.yaml` (Layered Defaults)
- **Sections**: Uses `default`, `development`, `production` headers.
- **Git**: Committed to the repository.
- **Content**: Non-sensitive shared logic and fallback values.

### C. Resolution Logic & Validation
1. **Validation**: Critical variables like `DATABASE_URL` are validated on startup using Dynaconf Validators.
2. **Merging**: Settings are merged across layers: `config.yaml [default]` -> `config.yaml [env]` -> `.env` -> `Environment Variables`.

```python
# genpulse/config.py
from dynaconf import Dynaconf
settings = Dynaconf(envvar_prefix="GENPULSE", settings_files=["config/config.yaml"])
```


