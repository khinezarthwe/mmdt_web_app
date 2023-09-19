#!/bin/bash

# Find the process ID (PID) of the Python application running on port 8000
PID=$(ps aux | grep "python3 manage.py runserver 0.0.0.0:8000" | grep -v grep | awk '{print $2}')

# Check if a PID was found
if [ -n "$PID" ]; then
    # Kill the process
    kill $PID
    echo "Process with PID $PID killed."
else
    echo "No process found running on port 8000."
fi
