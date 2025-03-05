from pathlib import Path
import time
import os
import shutil
import time
import signal

from utils.logger import *
from .uploader import *

# List files in directory
def list_files(directory):
    """Lists files in a directory."""
    files = {}
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if os.path.isfile(path):
            files[file] = os.path.getmtime(path)
    return files

# Copy file
def copy_file(file_path, target_directory):
    """Copy 'file_path' file to 'target_directory'."""
    function_name = inspect.currentframe().f_code.co_name
    Path(target_directory).mkdir(parents=True, exist_ok=True)
    shutil.copy(file_path, target_directory)
    log_message(function_name, "DEBUG", f"Copy file: {file_path} to: {target_directory}")

# Remove file
def remove_file(file_path):
    """Delete the 'file_path' file."""
    function_name = inspect.currentframe().f_code.co_name
    try:
        os.remove(file_path)
        log_message(function_name, "INFO", f"Remove file: {file_path}")
    except Exception as e:
        log_message(function_name, "ERROR", f"Failed to remove file: {file_path} - {e}")
        return

# Stop watcher
def stop_watcher_on_flag(flag_file): # pragma: no cover
    """Stop the watcher cleanly with a flag file."""
    function_name = inspect.currentframe().f_code.co_name
    if os.path.exists(flag_file):
        log_message(function_name, "WARNING", f"File '{flag_file}' has been found. Stop watcher.")
        # Renommer le fichier flag après l'arrêt (pour pouvoir relancer directement)
        os.rename(flag_file, 'start_watcher.flag')
        return True
    return False       

# Stop watcher on signal 
def stop_watcher_on_signal(signum, frame): # pragma: no cover
    """Stop watcher if process kill."""
    function_name = inspect.currentframe().f_code.co_name
    log_message(function_name, "WARNING", f"Signal {signum} received. Stop watcher.")
    sys.exit(0)  # Sortie du programme


# Watcher
def watch_directory(**kwargs): 
    """Watch the specified directory and process any JSON files created or modified."""
    function_name = inspect.currentframe().f_code.co_name
    
    # Get args
    path_input = kwargs.get("path_input")
    path_backup = kwargs.get("path_backup")
    config = kwargs.get("config")
    config_file = kwargs.get("config_file")
    
    previous_files = list_files(path_input)
    log_message(function_name, "INFO", f"Start watching directory: {path_input}")
    
    settings = load_configuration(config)
    recipients = settings["recipients"]
    
    try:
        while True:
            
            # Écoute du signal SIGTERM
            signal.signal(signal.SIGTERM, stop_watcher_on_signal) # pragma: no cover
    
            # Condition pour arrêt du watcher
            flag_file = 'stop_watcher.flag'
            if stop_watcher_on_flag(flag_file): # pragma: no cover
                send_mail_alert(recipients, "Diagho file_watcher has been stopped.")
                break
            
            time.sleep(5)  # Toutes les 5 secondes
            current_files = list_files(path_input)

            # Comparer les fichiers créés et modifiés
            new_files = set(current_files) - set(previous_files)
            modified_files = {f for f in current_files if f in previous_files and current_files[f] != previous_files[f]}

            # Si nouveau fichier ou ficher modifier :
            if new_files or modified_files:
                for file in new_files:
                    # TODO: gérer aussi .csv et .txt
                    if file_path.endswith((".json", ".tsv", ".csv", ".txt")):
                        file_path = os.path.join(path_input, file)
                        
                        log_message("NEW_FILE", "INFO", f"-----------------------------------------------------------------------------------------------")
                        log_message("NEW_FILE", "INFO", f"New file: {file_path}")
                        
                        try:
                            # Copier le fichier vers le répertoire backup
                            copy_file(file_path, path_backup)

                            # Traiter le fichier
                            log_message(function_name, "INFO", f"Processing file: {os.path.basename(file_path)}")
                            kwargs = {
                                "file_path": file_path,
                                "config": config,
                                "config_file": config_file
                            }
                            diagho_upload_file(**kwargs)

                            # Supprimer le fichier du répertoire 'input_data' après traitement
                            remove_file(file_path)
                            log_message(function_name, "INFO", f"Back to file_watcher...\n")

                        except Exception as e:
                            log_message(function_name, "ERROR", f"Failed to process file: {os.path.basename(file_path)} - {e}")

            # Mettre à jour la liste des fichiers pour la prochaine vérification
            previous_files = current_files

    except KeyboardInterrupt:
        print("Stop watching directory.")