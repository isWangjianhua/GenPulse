import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 1. Load Environment Variables from .env
load_dotenv()

# 2. Load Default Configuration from config.yaml
# 2. Configuration Paths
PACKAGE_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = PACKAGE_ROOT.parent.parent # Assuming src/genpulse structure

# Try multiple locations for config.yaml
config_paths = [
    Path.cwd() / "config.yaml",
    PROJECT_ROOT / "config.yaml",
    PACKAGE_ROOT / "config.yaml"
]

yaml_config = {}
for path in config_paths:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
        break

# Helper to get config with priority: Env Var > YAML > Default
def get_config(env_key, yaml_path, default=None):
    # Try Environment Variable
    val = os.getenv(env_key)
    if val is not None:
        return val
    
    # Try YAML nested path (e.g., "redis.url")
    keys = yaml_path.split('.')
    temp = yaml_config
    for k in keys:
        if isinstance(temp, dict) and k in temp:
            temp = temp[k]
        else:
            temp = None
            break
    
    if temp is not None:
        return temp
        
    return default

# --- Flattened Configuration Constants ---

ENV = get_config("ENV", "env", "dev")

# Redis
REDIS_URL = get_config("REDIS_URL", "redis.url", "redis://localhost:6379/0")
REDIS_TASK_QUEUE_NAME = get_config("REDIS_TASK_QUEUE_NAME", "redis.task_queue_name", "tasks:pending")
MQ_TYPE = get_config("MQ_TYPE", "mq.type", "redis")

# Database
DATABASE_URL = get_config("DATABASE_URL", "db.url", "postgresql+asyncpg://postgres:postgres@localhost:5432/genpulse")

# Storage
STORAGE_TYPE = get_config("STORAGE_TYPE", "storage.type", "local")
STORAGE_LOCAL_PATH = get_config("STORAGE_LOCAL_PATH", "storage.local_path", "data/assets")
STORAGE_BASE_URL = get_config("STORAGE_BASE_URL", "storage.base_url", "http://localhost:8000/assets")

# S3 (Optional)
S3_ENDPOINT_URL = get_config("S3_ENDPOINT_URL", "s3.endpoint_url")
S3_ACCESS_KEY = get_config("S3_ACCESS_KEY", "s3.access_key")
S3_SECRET_KEY = get_config("S3_SECRET_KEY", "s3.secret_key")
S3_BUCKET_NAME = get_config("S3_BUCKET_NAME", "s3.bucket_name", "genpulse")
S3_REGION_NAME = get_config("S3_REGION_NAME", "s3.region_name", "us-east-1")

# Providers
COMFY_URL = get_config("COMFY_URL", "providers.comfy_url", "http://127.0.0.1:8188")
DEFAULT_IMAGE_PROVIDER = get_config("DEFAULT_IMAGE_PROVIDER", "providers.default_image_provider", "volcengine")
DEFAULT_VIDEO_PROVIDER = get_config("DEFAULT_VIDEO_PROVIDER", "providers.default_video_provider", "volcengine")

# Derived Properties
REDIS_PREFIX = {
    "dev": "dev:",
    "test": "test:",
    "prod": "prod:"
}.get(ENV, "dev:")

