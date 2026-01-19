import pytest
import socket
import time
import requests

def wait_for_port(port: int, timeout: int = 30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
    return False

def test_comfyui_is_running():
    # Wait for ComfyUI port 8188
    print("Waiting for ComfyUI to start on port 8188...")
    assert wait_for_port(8188), "ComfyUI failed to start or is not listening on port 8188"
    
    # Check health/status if possible, or just index
    try:
        resp = requests.get("http://127.0.0.1:8188/")
        assert resp.status_code == 200
        print("ComfyUI is responding to HTTP requests!")
    except Exception as e:
        pytest.fail(f"ComfyUI port is open but HTTP request failed: {e}")
