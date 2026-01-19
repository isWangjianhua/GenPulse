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
@click.option('--with-comfy', is_flag=True, help="Automatically manage local ComfyUI process")
def start_worker(with_comfy):
    """Start only the Worker"""
    click.echo(f"Starting Worker (manage_comfy={with_comfy})...")
    from core.worker import Worker
    import asyncio
    worker = Worker(manage_comfy=with_comfy)
    
    # Handle signals for standalone worker
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: worker.stop())
        
    try:
        loop.run_until_complete(worker.run())
    finally:
        loop.close()

@cli.command()
@click.option('--api-port', default=8000, help="API Port")
def start_all(api_port):
    """Start API, Worker, and Local Libs (Dev Mode)"""
    click.echo("Starting All Services in Hybrid Mode...")
    
    processes = []
    
    # 1. Start Worker (with Local ComfyUI management)
    # We let the worker manage ComfyUI in this simplified "start-all"
    click.echo("Starting Task Worker with ComfyUI management...")
    worker_cmd = [sys.executable, "core/worker.py", "--with-comfy"]
    worker_p = subprocess.Popen(worker_cmd)
    processes.append(worker_p)

    # 2. Start API (blocking)
    try:
        click.echo(f"Starting API Server on port {api_port}...")
        uvicorn.run("core.gateway:app", host="0.0.0.0", port=api_port, reload=True)
    except KeyboardInterrupt:
        click.echo("\nShutting down all services...")
    finally:
        for p in processes:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
            click.echo(f"Terminated process {p.pid}")

if __name__ == "__main__":
    cli()
