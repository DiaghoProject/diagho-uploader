#!/bin/bash

# source venv
source venv/bin/activate

# Start file_watcher in background
nohup python main.py start_file_watcher &

