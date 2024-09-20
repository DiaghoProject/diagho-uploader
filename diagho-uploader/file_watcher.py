#!/usr/bin/python3

import time
import os
import yaml
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from process_file import *

import logging
logging.basicConfig(
    level=logging.DEBUG,                                                # Définir le niveau de log minimum
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',      # Format du message
    handlers=[
        logging.FileHandler('app.log'),                                 # Enregistrer les logs dans un fichier
        logging.StreamHandler()                                         # Afficher les logs sur la console
    ]
)


class MyHandler(FileSystemEventHandler):
    def __init__(self, target_directory, path_biofiles, config):
        self.target_directory = target_directory
        self.path_biofiles = path_biofiles
        self.config = config
        super().__init__()
        
    def on_created(self, event):
        if event.is_directory:
            return None
        else:
            file_path = event.src_path
            print(f"New file created: {file_path}")
            logging.info(f"New file created: {file_path}")
            
            ## TEST MAIL -----------------------
            recipients = self.config['emails']['recipients']
            content = "Test Email - New file created"
            send_mail_info(recipients, content)
            ## -----------------------
            
            if file_path.endswith('.tsv') or file_path.endswith('.file.json') or file_path.endswith('.files.json'):
                print(("File format : TSV or JSON"))
                self.copy_file(file_path)
                
                ## TODO #4 API authentification
                
                # self.process_file(file_path, self.path_biofiles)
                self.process_file(file_path, self.config)
                
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
    
    def process_file(self, file_path, config):
        print(f"Processing file: {file_path}")
        try:
            logging.info(f"Processing file: {file_path}")
            diagho_process_file(file_path, config)
        except Exception as e:
            print(f"Failed to process file: {e}")
            # logging.error(f"Failed to process file: {e}")
            
            
def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def main():
    # Load configuration file
    config = load_config("config/config.yaml")
    
    # Directories : JSON files, VCFs/BEDs file, backup
    path_input = config.get("input_data", ".")
    path_biofiles = config.get("input_biofiles", ".")
    path_backup = config.get("backup_data_files")
    if not os.path.exists(path_backup):
        os.makedirs(path_backup)

    # Define wtacher
    event_handler = MyHandler(target_directory=path_backup, path_biofiles=path_biofiles, config=config)
    observer = Observer()
    observer.schedule(event_handler, path_input, recursive=False)

    # Start wtacher
    observer.start()
    print(f"Watching directory: {path_input}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    
if __name__ == "__main__":
    main()
    
