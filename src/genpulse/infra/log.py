import sys
import logging
from pathlib import Path
from loguru import logger
from genpulse.config import settings

class InterceptHandler(logging.Handler):
    """
    Default handler from loguru documentation for intercepting standard logging messages.
    See: https://loguru.readthedocs.io/en/stable/overview.html#intercepting-standard-logging-messages
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """
    Initialize loguru with configuration from config.yaml and intercept standard logging.
    """
    log_cfg = settings.get("LOGGING", {})
    log_level = log_cfg.get("level", "INFO").upper()
    log_dir = Path(log_cfg.get("log_dir", "logs"))
    save_to_file = log_cfg.get("save_to_file", True)
    
    # 1. Remove default loguru handler
    logger.remove()

    # 2. Add dynamic console handler with colors
    # Format: Time | Level | Module | Task_ID (if any) | Message
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(sys.stderr, level=log_level, format=fmt, colorize=True)

    # 3. Add file handlers if enabled
    if save_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main log file (rotation & retention)
        logger.add(
            log_dir / "genpulse.log",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=log_cfg.get("rotation", "500 MB"),
            retention=log_cfg.get("retention", "10 days"),
            compression="zip",
            encoding="utf-8"
        )
        
        # Error only log file
        logger.add(
            log_dir / "error.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )

    # 4. Intercept standard logging from other libraries (uvicorn, sqlalchemy, etc.)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Specifically intercept some common noisy loggers to ensure they use our loguru format
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "sqlalchemy.engine"]:
        _logger = logging.getLogger(name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

    logger.info(f"Logging initialized. Level: {log_level}, Save to file: {save_to_file}")

# Export for convenience
log = logger
