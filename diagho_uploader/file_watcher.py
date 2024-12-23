#!/usr/bin/python3

import time
import os
import yaml
import shutil

from .process_file import *

import logging

logs_directory = "logs"
if not os.path.exists(logs_directory):
    os.makedirs(logs_directory)
log_filename = os.path.join(logs_directory, 'app.log')
    
logging.basicConfig(
    level=logging.INFO,                                                 # Définir le niveau de log minimum
    format='[%(asctime)s][%(levelname)s][%(name)s] %(message)s',        # Format du message
    handlers=[
        logging.FileHandler(log_filename),                              # Enregistrer les logs dans un fichier
        logging.StreamHandler()                                         # Afficher les logs sur la console
    ]
)

            
# Load configuration            
def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

# List files in directory
def list_files(directory):
    files = {}
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if os.path.isfile(path):
            files[file] = os.path.getmtime(path)
    return files

# Copy file
def copy_file(file_path, target_directory):
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    shutil.copy(file_path, target_directory)
    print(f"File copied to: {target_directory}")

# Remove file
def remove_file(file_path):
    try:
        os.remove(file_path)
        print(f"File removed from: {file_path}")
    except Exception as e:
        print(f"Failed to remove file: {e}")

# Watch directory
def watch_directory(path_input, path_backup, path_biofiles, config):
    
    previous_files = list_files(path_input)
    print(f"Watching directory: {path_input}")
    
    try:
        while True:
            time.sleep(5)
            current_files = list_files(path_input)
            
            new_files = set(current_files) - set(previous_files)
            modified_files = {f for f in current_files if f in previous_files and current_files[f] != previous_files[f]}
            
            if new_files:
                print(f"Fichiers créés : {new_files}")
                
                for file in new_files:
                    if file.endswith(".json") :
                        file_path = os.path.join(path_input, file)
                        print(f"Processing file: {file_path}")
                        try:
                            # Copy file to backup
                            copy_file(file_path, path_backup)
                            
                            # Process file
                            diagho_process_file(file_path, config)
                            
                            # Remove file from directory
                            remove_file(file_path)
                            
                        except Exception as e:
                            print(f"Failed to process file: {e}")
            
            if modified_files:
                print(f"Modified files : {modified_files}")
            
            previous_files = current_files

    except KeyboardInterrupt:
        print("Stop watching directory.")

    
def main():
    # Load configuration file
    config = load_config("config/config.yaml")
    
    # Input directories
    path_input = config.get("input_data", ".")
    path_biofiles = config.get("input_biofiles", ".")
    path_backup = config.get("backup_data")
    if not os.path.exists(path_backup):
        os.makedirs(path_backup)

    # Watch directory
    watch_directory(path_input, path_backup, path_biofiles, config)
    
if __name__ == "__main__":
    main()
    
