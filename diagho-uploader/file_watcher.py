import time
import os
import json
import yaml
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



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
            print(f"Process file...")
            
            self.copy_file(file_path)
            
            # Traiter le fichier
            self.process_file(file_path)
            
            time.sleep(3)
            
            self.remove_file(file_path)

    
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
                data = json.load(file)
                # Parcourir chaque élément du JSON et lancer une fonction
                for item in data:
                    self.process_item(item)
        except Exception as e:
            print(f"Failed to process file: {e}")
            
    def process_item(self, item):
        # Fonction spécifique pour traiter chaque élément du JSON
        print(f"Processing item: {item}")
        
            
def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

if __name__ == "__main__":
    config = load_config("config/config.yaml")
    path_input = config.get("input_data", ".")  # Par défaut, utilise le répertoire courant si non spécifié
    path_backup = config.get("backup_data_files", ".")


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
