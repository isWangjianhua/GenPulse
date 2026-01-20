from dynaconf import Dynaconf, Validator
from pathlib import Path

# 1. Define Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 2. Instantiate Dynaconf
# It will automatically look for config.yaml and .env files
settings = Dynaconf(
    envvar_prefix="GENPULSE",      # Look for GENPULSE_VAR in .env/Shell
    settings_files=["config/config.yaml"], # Load shared defaults from config folder
    environments=True,             # Enable [default, development, production] sections
    load_dotenv=True,              # Allow .env files
    env_switcher="ENV_FOR_DYNACONF", # Change env via ENV_FOR_DYNACONF=production
    root_path=PROJECT_ROOT,
)

# 3. Define Validation Rules
settings.validators.register(
    # Ensure critical connection strings are present
    Validator("REDIS_URL", must_exist=True, default="redis://localhost:6379/0"),
    Validator("DATABASE_URL", must_exist=True),
    # Ensure storage type is valid
    Validator("STORAGE.TYPE", is_in=["local", "s3"], default="local"),
)

# 4. Trigger Validation
settings.validators.validate()

# --- Export Constants for Backward Compatibility ---
# This ensures existing code (e.g., in worker.py or router.py) doesn't break.

ENV = settings.get("ENV", "dev")
REDIS_URL = settings.REDIS_URL
DATABASE_URL = settings.DATABASE_URL
REDIS_TASK_QUEUE_NAME = settings.REDIS.TASK_QUEUE_NAME
MQ_TYPE = settings.get("MQ_TYPE", "redis")

STORAGE_TYPE = settings.STORAGE.TYPE
STORAGE_LOCAL_PATH = settings.STORAGE.LOCAL_PATH
STORAGE_BASE_URL = settings.STORAGE.BASE_URL

COMFY_URL = settings.PROVIDERS.COMFY_URL
DEFAULT_IMAGE_PROVIDER = settings.PROVIDERS.DEFAULT_IMAGE_PROVIDER
DEFAULT_VIDEO_PROVIDER = settings.PROVIDERS.DEFAULT_VIDEO_PROVIDER

# Secrets (Automatically mapped from GENPULSE_VOLC_ACCESS_KEY etc.)
VOLC_ACCESS_KEY = settings.get("VOLC_ACCESS_KEY")
VOLC_SECRET_KEY = settings.get("VOLC_SECRET_KEY")

S3_ENDPOINT_URL = settings.get("S3_ENDPOINT_URL")
S3_ACCESS_KEY = settings.get("S3_ACCESS_KEY")
S3_SECRET_KEY = settings.get("S3_SECRET_KEY")
S3_BUCKET_NAME = settings.get("S3_BUCKET_NAME", "genpulse")
S3_REGION_NAME = settings.get("S3_REGION_NAME", "us-east-1")

# Derived settings
REDIS_PREFIX = {
    "development": "dev:",
    "testing": "test:",
    "production": "prod:"
}.get(settings.current_env.lower(), "dev:")
