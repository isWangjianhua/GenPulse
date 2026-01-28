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
    from genpulse.routers.task import router as task_router
    app.include_router(task_router)
    
    # 3. Setup Admin Dashboard
    from genpulse.infra.database.engine import engine
    from genpulse.admin import init_admin
    init_admin(app, engine)
    
    # 4. Storage Router
    from genpulse.routers.storage import router as storage_router
    app.include_router(storage_router)

    @app.get("/health")
    async def health_check(full: bool = False):
        """
        Health check endpoint.
        GET /health -> Quick liveness probe.
        GET /health?full=true -> Deep inspection (Redis, DB, Workers).
        """
        status = {"status": "ok", "version": "0.1.0"}
        
        if not full:
            return status

        details = {}
        # 1. Check Redis/MQ
        try:
            from genpulse.infra.mq import get_mq
            mq = get_mq()
            await mq.ping()
            details["redis"] = "ok"
        except Exception as e:
            details["redis"] = f"failed: {str(e)}"
            status["status"] = "degraded"

        # 2. Check Celery Workers
        try:
            from genpulse.infra.mq.celery_app import celery_app
            import asyncio
            # Run blocking control command in thread
            # ping() returns a list of dictionaries like [{'celery@worker1': {'ok': 'pong'}}]
            pongs = await asyncio.to_thread(celery_app.control.ping, timeout=1.5)
            details["workers_online"] = len(pongs) if pongs else 0
            details["workers_raw"] = pongs
        except Exception as e:
            details["workers"] = f"check_failed: {str(e)}"
            # Don't mark as degraded if just ping timeout, but maybe warning?

        status["details"] = details
        return status

    @app.get("/")
    async def root():
        return {"app": "GenPulse", "version": "0.1.0"}

    return app


