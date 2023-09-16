#!/bin/bash

# Activate the virtual environment
source /home/ubuntu/mmdt-web-app/myenv/bin/activate 

# Change directory to the location of manage.py
cd /home/ubuntu/mmdt-web-app/mmdt
python3 manage.py runserver 0.0.0.0:8000
