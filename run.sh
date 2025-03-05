#!/bin/bash

# Pre-require
# Créer venv et installer les dépendances
python -m venv venv
pip install -r requirements.txt

# source venv
source venv/bin/activate

# Start file_watcher in background
nohup python main.py start_file_watcher &
