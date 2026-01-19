import subprocess
import os
import time
import logging
from pathlib import Path
from typing import Optional
from core.config import settings

logger = logging.getLogger(__name__)

class ComfyProcessManager:
    def __init__(self, workspace_path: str = "libs/comfyui", port: int = 8188):
        self.workspace_path = Path(workspace_path).resolve()
        self.port = port
        self.process: Optional[subprocess.Popen] = None

    def install(self):
        """Install ComfyUI via git clone (non-interactive)"""
        if not (self.workspace_path / "main.py").exists():
            logger.info(f"Installing ComfyUI to {self.workspace_path}...")
            try:
                # 1. Git Clone
                if not self.workspace_path.exists():
                    self.workspace_path.mkdir(parents=True)
                
                # Clone repository
                subprocess.check_call([
                    "git", "clone", "https://github.com/comfyanonymous/ComfyUI.git", "."
                ], cwd=self.workspace_path)
                
                # 2. Install dependencies
                # We install them into the CURRENT uv environment
                subprocess.check_call([
                    "uv", "pip", "install", "-r", "requirements.txt"
                ], cwd=self.workspace_path)
                
                logger.info("ComfyUI installed successfully.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install ComfyUI: {e}")
                raise

    def start(self, cpu_only: bool = True):
        """Start ComfyUI subprocess"""
        if self.is_running():
            logger.info("ComfyUI is already running.")
            return

        cmd = [
            "uv", "run", "comfy", 
            "--workspace", str(self.workspace_path), 
            "launch", 
            "--port", str(self.port),
            "--background" 
        ]
        
        if cpu_only:
             # comfy launch arguments are passed after -- 
             # wait, comfy-cli launch might handle it differently.
             # According to docs, we pass arguments to ComfyUI.
             # Let's try passing --cpu directly to launch if supported, or via -- --cpu
             cmd.extend(["--", "--cpu"])

        logger.info(f"Starting ComfyUI with command: {' '.join(cmd)}")
        
        # We start it as a detached process or managed subprocess
        # For now, let's keep it simple: managed subprocess but non-blocking here?
        # comfy launch --background might detach it.
        # Let's just use Popen directly on main.py if comfy-cli is complex to wrap
        
        # ALTERNATIVE: Direct python launch to have better control
        # python main.py --port 8188 --cpu
        
        main_py = self.workspace_path / "main.py"
        if not main_py.exists():
            self.install()
        
        launch_args = ["python", str(main_py), "--port", str(self.port)]
        if cpu_only:
            launch_args.append("--cpu")
            
        # We need to make sure we use the same venv or environment
        # If running via 'uv run', 'python' should be the venv python
        
        try:
            self.process = subprocess.Popen(
                launch_args,
                cwd=self.workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Wait a bit to check for immediate failure
            time.sleep(2)
            if self.process.poll() is not None:
                _, err = self.process.communicate()
                raise RuntimeError(f"ComfyUI failed to start: {err.decode()}")
                
            logger.info(f"ComfyUI started with PID {self.process.pid}")
            
        except Exception as e:
            logger.error(f"Failed to start ComfyUI: {e}")
            raise

    def stop(self):
        """Stop key ComfyUI process"""
        if self.process and self.process.poll() is None:
            logger.info("Stopping ComfyUI...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("ComfyUI stopped.")

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None
