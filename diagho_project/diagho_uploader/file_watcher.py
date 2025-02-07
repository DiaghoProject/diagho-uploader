from pathlib import Path
import time
import os
import yaml
import shutil
from datetime import datetime
import time
import signal

# Gestion des logs
from common.logger_config import logger 
from common.log_utils import *

from .process_file import *




# List files in directory
def list_files(directory):
    """Liste les fichiers d'un répertoire."""
    files = {}
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if os.path.isfile(path):
            files[file] = os.path.getmtime(path)
    return files

# Copy file
def copy_file(file_path, target_directory):
    """Copier le fichier 'file_path' dans 'target_directory'."""
    function_name = inspect.currentframe().f_code.co_name
    Path(target_directory).mkdir(parents=True, exist_ok=True)
    shutil.copy(file_path, target_directory)
    log_message(function_name, "INFO", f"Copy file: {file_path} to: {target_directory}")

# Remove file
def remove_file(file_path):
    """Supprimer le fichier 'file_path'."""
    function_name = inspect.currentframe().f_code.co_name
    try:
        os.remove(file_path)
        log_message(function_name, "INFO", f"Remove file: {file_path}")
    except Exception as e:
        log_message(function_name, "ERROR", f"Failed to remove file: {file_path} - {e}")
        return

# Stop watcher
def stop_watcher_on_flag(flag_file): # pragma: no cover
    """Arrêter proprement le watcher avec un fichier de flag."""
    function_name = inspect.currentframe().f_code.co_name
    if os.path.exists(flag_file):
        log_message(function_name, "WARNING", f"File '{flag_file}' has been found. Stop watcher.")
        # Renommer le fichier flag après l'arrêt (pour pouvoir relancer directement)
        os.rename(flag_file, 'start_watcher.flag')
        return True
    return False       

# Stop watcher on signal 
def stop_watcher_on_signal(signum, frame): # pragma: no cover
    """Arrêter le watcher si kill du process."""
    function_name = inspect.currentframe().f_code.co_name
    log_message(function_name, "WARNING", f"Signal {signum} received. Stop watcher.")
    sys.exit(0)  # Sortie du programme


# Watcher
def watch_directory(path_input, path_backup, path_biofiles, config, config_file): 
    """
    Surveille le répertoire spécifié et traite les fichiers JSON créés ou modifiés.
    """
    function_name = inspect.currentframe().f_code.co_name
    
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

            # Si nouveau fichier :
            if new_files:
                for file in new_files:
                    if file.endswith(".json") or file.endswith(".tsv"): # prendre en compte uniquement les JSON ou TSV
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

            # SI fichier modifié :
            if modified_files:
                for file in modified_files:
                    file_path = os.path.join(path_input, file)
                    
                    log_message("NEW_FILE", "INFO", f"-----------------------------------------------------------------------------------------------")
                    log_message("MODIFIED_FILE", "INFO", f"New file: {file_path}")
                        
                    try:
                        # Copier le fichier vers le répertoire backup
                        copy_file(file_path, path_backup)

                        # Traiter le fichier
                        log_message(function_name, "INFO", f"Processing file: {os.path.basename(file_path)}")
                        kwargs = {
                            "file_path": file_path,
                            "config": config,
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