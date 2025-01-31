#!/bin/bash

source venv/bin/activate

cd diagho_project

# Start file_watcher
python main.py start_file_watcher


# Create JSON
python main.py create_inputs \
    --input_file $INPUT_TSV \
    --output_file $OUTPUT_JSON