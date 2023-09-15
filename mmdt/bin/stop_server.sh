#!/bin/bash

PID=$(lsof -ti :8000)
if [ -z "$PID" ]; then
    echo "Server is not running."
else
    echo "Stopping server with PID: $PID"
    kill "$PID"
    echo "Server stopped."
fi
