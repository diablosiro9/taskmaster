#!/bin/bash

CONFIG_FILE="school.yaml"

start() {
    echo "🔹 Starting TaskMaster (mandatory foreground)..."
    # Foreground direct, ignore SIGHUP sur le shell parent
    trap '' HUP
    python3 main.py "$CONFIG_FILE"
}

case "$1" in
    start)
        start
        ;;
    *)
        echo "Usage: $0 start"
        ;;
esac
