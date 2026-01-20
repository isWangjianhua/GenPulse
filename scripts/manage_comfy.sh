#!/bin/bash

# ComfyUI Sidecar Management Script
# This script manages a local ComfyUI instance independent of GenPulse core logic.

WORKSPACE="libs/ComfyUI"
PORT=8188

function install_comfy() {
    echo "Checking ComfyUI installation in $WORKSPACE..."
    if [ -f "$WORKSPACE/main.py" ]; then
        echo "ComfyUI is already installed."
    else
        echo "Installing ComfyUI via comfy-cli..."
        comfy --workspace "$WORKSPACE" install
    fi
}

function start_comfy() {
    install_comfy
    echo "Starting ComfyUI on port $PORT (CPU mode)..."
    echo "Access URL: http://127.0.0.1:$PORT"
    
    # Use the absolute path for the config file to avoid resolution issues
    CONFIG_PATH="$(pwd)/config/comfy/extra_model_paths.yaml"
    
    # Note: comfy-cli launch passes extra arguments after '--' to main.py
    comfy --workspace "$WORKSPACE" launch -- --port "$PORT" --cpu --extra-model-paths-config "$CONFIG_PATH"
}

case "$1" in
    install)
        install_comfy
        ;;
    start)
        start_comfy
        ;;
    *)
        echo "Usage: $0 {install|start}"
        echo ""
        echo "Examples:"
        echo "  ./scripts/manage_comfy.sh start    # Install if missing and start ComfyUI"
        echo "  ./scripts/manage_comfy.sh install  # Only pre-install"
        exit 1
esac
