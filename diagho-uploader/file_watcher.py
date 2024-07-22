#!/usr/bin/python3

import time
import os
import yaml
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from process_file import *

class MyHandler(FileSystemEventHandler):
    def __init__(self, target_directory):
        self.target_directory = target_directory
        super().__init__()
        
    def on_created(self, event):
        if event.is_directory:
            return None
        else:
            file_path = event.src_path
            print(f"New file created: {file_path}")
            
            if file_path.endswith('.tsv') or file_path.endswith('.json'):
                print(("File format : TSV or JSON"))
                self.copy_file(file_path)
                
                self.process_file(file_path)
                
                time.sleep(3)
                
                self.remove_file(file_path)
                
            else:
                print(f"Ignored file: {file_path}")
            
           
    def copy_file(self, file_path):
        if not os.path.exists(self.target_directory):
            os.makedirs(self.target_directory)
        shutil.copy(file_path, self.target_directory)
        print(f"File copied to: {self.target_directory}")
        
    def remove_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"File removed from: {file_path}")
        except Exception as e:
            print(f"Failed to remove file: {e}")
    
    def process_file(self, file_path):
        print(f"Processing file: {file_path}")
        try:
            with open(file_path, 'r') as file:
                diagho_process_file(file_path, path_biofiles)
        except Exception as e:
            print(f"Failed to process file: {e}")
            
            
def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

if __name__ == "__main__":
    config = load_config("config/config.yaml")
    path_input = config.get("input_data", ".")
    path_biofiles = config.get("input_biofiles", ".")
    path_backup = config.get("backup_data_files")
    if not os.path.exists(path_backup):
            os.makedirs(path_backup)


    event_handler = MyHandler(target_directory=path_backup)
    observer = Observer()
    observer.schedule(event_handler, path_input, recursive=False)

    observer.start()
    print(f"Watching directory: {path_input}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
