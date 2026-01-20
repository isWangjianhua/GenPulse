from dynaconf import Dynaconf, Validator
from pathlib import Path

# 1. Define Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 2. Instantiate Dynaconf
settings = Dynaconf(
    envvar_prefix="GENPULSE",
    settings_files=["config/config.yaml"],
    environments=True,
    load_dotenv=True,
    env_switcher="ENV_FOR_DYNACONF",
    root_path=PROJECT_ROOT,
)

# 3. Define Validation Rules
settings.validators.register(
    Validator("DATABASE_URL", must_exist=True),
    Validator("REDIS.URL", must_exist=True, default="redis://localhost:6379/0"),
    Validator("STORAGE.TYPE", is_in=["local", "s3"], default="local"),
    Validator("LOGGING.LEVEL", default="INFO"),
    Validator("PROVIDERS.DEFAULT_IMAGE_PROVIDER", default="volcengine"),
)

# 4. Trigger Validation
settings.validators.validate()

# --- Helpers ---
def get_env():
    return settings.get("ENV", "development").lower()

def is_dev():
    return get_env() in ["dev", "development"]

# --- Derived / Exported Constants ---
# Keeping these for ease of use across the app
ENV = get_env()
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS.URL

STORAGE_TYPE = settings.STORAGE.TYPE
STORAGE_LOCAL_PATH = settings.STORAGE.LOCAL_PATH
STORAGE_BASE_URL = settings.STORAGE.BASE_URL

COMFY_URL = settings.PROVIDERS.get("COMFY_URL", "http://127.0.0.1:8188")
DEFAULT_IMAGE_PROVIDER = settings.PROVIDERS.DEFAULT_IMAGE_PROVIDER
DEFAULT_VIDEO_PROVIDER = settings.PROVIDERS.DEFAULT_VIDEO_PROVIDER

# Redis Keys & Queues
REDIS_PREFIX = f"{ENV}:"
TASK_QUEUE_NAME = f"{REDIS_PREFIX}tasks"
TASK_STATUS_PREFIX = f"{REDIS_PREFIX}task_status:"
