#!/bin/bash

# Universal watch script using watchexec
# Usage: ./watch.sh <file>
# Example: ./watch.sh case.py

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

FILE_TO_WATCH="$1"

# Check if watchexec is installed
if ! command -v watchexec &> /dev/null; then
    echo "Installing watchexec..."
    cargo install watchexec-cli
fi

echo "Watching $FILE_TO_WATCH..."
watchexec -w "$FILE_TO_WATCH" -c -- uv run "$FILE_TO_WATCH"