import click
import uvicorn
import subprocess
import os
import signal
import sys
import time
from typing import List

@click.group()
def cli():
    pass

@cli.command()
@click.option('--host', default="0.0.0.0", help="API Host")
@click.option('--port', default=8000, help="API Port")
@click.option('--reload', is_flag=True, default=True, help="Enable Uvicorn reload")
def start_api(host, port, reload):
    """Start only the API Server"""
    click.echo(f"Starting API Server on {host}:{port}...")
    uvicorn.run("core.gateway:app", host=host, port=port, reload=reload)

@cli.command()
def start_worker():
    """Start only the Worker"""
    click.echo("Starting Worker...")
    from core.worker import Worker
    import asyncio
    worker = Worker()
    asyncio.run(worker.run())

@cli.command()
@click.option('--api-port', default=8000, help="API Port")
def start_all(api_port):
    """Start API, Worker, and Local Libs (Dev Mode)"""
    click.echo("Starting All Services in Hybrid Mode...")
    
    processes = []
    
    # 1. Start Local ComfyUI if it exists
    comfy_script = os.path.join("libs", "comfyui", "main.py")
    if os.path.exists(comfy_script):
        click.echo(f"Launching Local ComfyUI from {comfy_script}...")
        p = subprocess.Popen([sys.executable, comfy_script])
        processes.append(p)
    else:
        click.echo("Local ComfyUI not found, skipping engine startup.")

    # 2. Start Worker (as a separate subprocess for true parallel execution in start-all)
    click.echo("Starting Task Worker...")
    worker_p = subprocess.Popen([sys.executable, "core/worker.py"])
    processes.append(worker_p)

    # 3. Start API (blocking)
    try:
        click.echo(f"Starting API Server on port {api_port}...")
        uvicorn.run("core.gateway:app", host="0.0.0.0", port=api_port, reload=True)
    except KeyboardInterrupt:
        click.echo("\nShutting down all services...")
    finally:
        for p in processes:
            p.terminate()
            click.echo(f"Terminated process {p.pid}")

if __name__ == "__main__":
    cli()
