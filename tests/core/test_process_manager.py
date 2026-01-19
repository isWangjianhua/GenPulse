import pytest
import os
import subprocess
from unittest.mock import MagicMock, patch
from core.process_manager import ComfyProcessManager
from pathlib import Path

@pytest.fixture
def process_manager(tmp_path):
    # Use a temp directory for workspace to avoid messing with real libs/
    workspace = tmp_path / "comfyui"
    workspace.mkdir()
    (workspace / "main.py").write_text("print('mock comfyui')")
    return ComfyProcessManager(workspace_path=str(workspace), port=9999)

def test_pm_init(process_manager):
    assert "comfyui" in str(process_manager.workspace_path)
    assert process_manager.port == 9999
    assert process_manager.process is None

@patch("subprocess.Popen")
def test_pm_start(mock_popen, process_manager):
    mock_process = MagicMock()
    mock_process.poll.return_value = None # Running
    mock_popen.return_value = mock_process
    
    process_manager.start(cpu_only=True)
    
    assert process_manager.is_running()
    # Check if extra_model_paths.yaml was created
    config_path = process_manager.workspace_path / "extra_model_paths.yaml"
    assert config_path.exists()
    assert "base_path: ../../models" in config_path.read_text()
    
    mock_popen.assert_called()

@patch("subprocess.Popen")
def test_pm_stop(mock_popen, process_manager):
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    process_manager.process = mock_process
    
    process_manager.stop()
    
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()
