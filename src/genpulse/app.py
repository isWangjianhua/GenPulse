from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from loguru import logger
from genpulse.infra.database.engine import init_db
from genpulse import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"DB initialization failed: {e}")
    yield

def create_api() -> FastAPI:
    """FastAPI Application Factory"""
    app = FastAPI(title="GenPulse API", lifespan=lifespan)
    
    # 1. Mount static files
    os.makedirs(config.STORAGE_LOCAL_PATH, exist_ok=True)
    app.mount("/assets", StaticFiles(directory=config.STORAGE_LOCAL_PATH), name="assets")

    # 2. Register feature routers
    from genpulse.features.task.router import router as task_router
    app.include_router(task_router)

    # Health check
    @app.get("/health")
    async def health_check():
        from genpulse.infra.mq import get_mq
        mq = get_mq()
        try:
            await mq.ping()
            return {"status": "ok", "services": {"mq": "connected", "db": "up"}}
        except Exception as e:
            return {"status": "partial", "error": str(e)}

    @app.get("/")
    async def root():
        return {"app": "GenPulse", "version": "0.1.0"}

    return app

def create_worker():
    """Worker Application Factory"""
    from genpulse.worker import Worker
    return Worker()
