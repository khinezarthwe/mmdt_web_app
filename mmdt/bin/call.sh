#!/bin/bash

# Activate the virtual environment
source /home/ubuntu/mmdt-web-app/myenv/bin/activate 
#python script.py

# Change directory to the location of manage.py
cd /home/ubuntu/mmdt-web-app/mmdt
#python3 manage.py  migrate
# Run the Django development server
python3 manage.py runserver
