import click
import uvicorn
import asyncio
import logging
from genpulse.app import create_api, create_worker
from genpulse.infra.database.engine import init_db as _init_db

logger = logging.getLogger("GenPulseCLI")

@click.group()
def cli():
    """GenPulse Management CLI"""
    logging.basicConfig(level=logging.INFO)

@cli.command()
def init_db():
    """Initialize Database Tables"""
    click.echo("Initializing Database...")
    asyncio.run(_init_db())
    click.echo("Database Initialized.")

@cli.command()
@click.option('--host', default="0.0.0.0")
@click.option('--port', default=8000)
@click.option('--reload', is_flag=True, default=False)
def api(host, port, reload):
    """Start the API Server"""
    # Lifespan in FastAPI handles DB init
    if reload:
        uvicorn.run("genpulse.app:create_api", host=host, port=port, reload=True, factory=True)
    else:
        app = create_api()
        uvicorn.run(app, host=host, port=port)

@cli.command()
def worker():
    """Start the Worker Process"""
    click.echo("Starting Worker...")
    worker = create_worker()
    
    import signal
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: worker.stop())
        
    asyncio.run(worker.run())

@cli.command()
def dev():
    """Start API and Worker in a combined process (recommended for Local Dev)"""
    click.echo("Starting GenPulse in Development Mode...")
    
    async def run_all():
        # 1. Ensure DB
        await _init_db()
        
        # 2. Setup Worker
        worker = create_worker()
        
        # 3. Setup API (direct uvicorn instance)
        config = uvicorn.Config(create_api(), host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        
        # 4. Run both concurrently
        await asyncio.gather(
            server.serve(),
            worker.run()
        )

    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    cli()
