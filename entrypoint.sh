#!/bin/bash
set -e +x

OPTION="$1"
#SHIFT

case "$OPTION" in
  "api")
    echo "Executing API Command"
    /usr/local/bin/uvicorn api.main:app --host 0.0.0.0 --port 8080
    ;;
  "listener")
    echo "Executing LISTENER Flow"
    /usr/local/bin/python3 -u /app/api/handlers/web_event_handler.py
    ;;
  *)
    echo "Usage: $0 <command>"
    exit 1
    ;;
esac