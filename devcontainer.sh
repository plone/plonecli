#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_FOLDER="$(cd "$(dirname "$0")" && pwd)"

usage() {
    echo "Usage: $0 {start|stop|rebuild|bash}"
    echo ""
    echo "  start    Start the devcontainer"
    echo "  stop     Stop and remove the devcontainer"
    echo "  rebuild  Rebuild (no cache) and start the devcontainer"
    echo "  bash     Open a bash shell inside the running devcontainer"
    exit 1
}

cmd_start() {
    echo "Starting devcontainer..."
    devcontainer up --workspace-folder "$WORKSPACE_FOLDER"
}

cmd_stop() {
    echo "Stopping devcontainer..."
    CONTAINER_IDS=$(docker ps -q --filter "label=devcontainer.local_folder=$WORKSPACE_FOLDER")
    if [ -n "$CONTAINER_IDS" ]; then
        docker rm -f $CONTAINER_IDS
        echo "Devcontainer stopped."
    else
        echo "No running devcontainer found."
    fi
}

cmd_bash() {
    devcontainer exec --workspace-folder "$WORKSPACE_FOLDER" bash
}

cmd_rebuild() {
    echo "Rebuilding devcontainer (no cache)..."
    devcontainer build --workspace-folder "$WORKSPACE_FOLDER" --no-cache
    echo "Starting devcontainer (replacing existing)..."
    devcontainer up --workspace-folder "$WORKSPACE_FOLDER" --remove-existing-container
}

case "${1:-}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    rebuild) cmd_rebuild ;;
    bash)    cmd_bash ;;
    *)       usage ;;
esac
