import click
import uvicorn
import asyncio
import logging
from genpulse.app import create_api
from genpulse.infra.database.engine import init_db as _init_db

from genpulse.infra.log import setup_logging

logger = logging.getLogger("GenPulseCLI")

@click.group()
def cli():
    """GenPulse Management CLI"""
    setup_logging()

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
    """Start the Celery Worker Process"""
    click.echo("Starting Celery Worker...")
    import subprocess
    import sys
    # Use subprocess to run celery
    cmd = [sys.executable, "-m", "celery", "-A", "genpulse.infra.mq.celery_app", "worker", "--loglevel=info"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

@cli.command()
@click.option('--port', default=5555, help='Port to run Flower on')
def monitor(port):
    """Start Flower Dashboard for Real-time Monitoring"""
    click.echo(f"Starting Celery Flower on http://localhost:{port}")
    import subprocess
    import sys
    # celery -A genpulse.infra.mq.celery_app flower --port=5555
    cmd = [
        sys.executable, "-m", "celery", 
        "-A", "genpulse.infra.mq.celery_app", 
        "flower", 
        f"--port={port}"
    ]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

@cli.command()
def dev():
    """Start API and Worker in a combined process (recommended for Local Dev)"""
    click.echo("Starting GenPulse in Development Mode (API + Celery)...")
    import subprocess
    import sys
    
    # 1. Ensure DB (run async in sync context)
    asyncio.run(_init_db())
    
    # 2. Start Processes
    # API
    api_cmd = [sys.executable, "-m", "uvicorn", "genpulse.app:create_api", "--host", "0.0.0.0", "--port", "8000", "--reload", "--factory"]
    api_proc = subprocess.Popen(api_cmd)
    
    # Worker
    worker_cmd = [sys.executable, "-m", "celery", "-A", "genpulse.infra.mq.celery_app", "worker", "--loglevel=info"]
    worker_proc = subprocess.Popen(worker_cmd)
    
    click.echo(f"Services started. API: {api_proc.pid}, Worker: {worker_proc.pid}")
    
    try:
        api_proc.wait()
        worker_proc.wait()
    except KeyboardInterrupt:
        click.echo("\nStopping services...")
        api_proc.terminate()
        worker_proc.terminate()
    except Exception as e:
        click.echo(f"Error: {e}")
        api_proc.terminate()
        worker_proc.terminate()

if __name__ == "__main__":
    cli()
