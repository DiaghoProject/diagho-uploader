import time
import os
import yaml
import shutil
from datetime import datetime
import time

# Logs
from common.logger_config import logger 

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
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    shutil.copy(file_path, target_directory)
    print(f"File copied to: {target_directory}")

# Remove file
def remove_file(file_path):
    """Supprimer le fichier 'file_path'."""
    try:
        os.remove(file_path)
        print(f"File removed from: {file_path}")
    except Exception as e:
        print(f"Failed to remove file: {e}")
        

# Watcher
def watch_directory(path_input, path_backup, path_biofiles, config):
    """
    Surveille le répertoire spécifié et traite les fichiers JSON créés ou modifiés.
    """
    previous_files = list_files(path_input)
    logger = logging.getLogger("FILE_WATCHER")
    logger.info("Start watching directory: %s", path_input)
    
    try:
        while True:
            time.sleep(5)  # Toutes les 5 secondes
            current_files = list_files(path_input)

            # Comparer les fichiers créés et modifiés
            new_files = set(current_files) - set(previous_files)
            modified_files = {f for f in current_files if f in previous_files and current_files[f] != previous_files[f]}

            # Si nouveau fichier :
            if new_files:
                for file in new_files:
                    if file.endswith(".json"): # prendre en compte uniquement les JSON
                        file_path = os.path.join(path_input, file)
                        
                        logger = logging.getLogger("NEW_FILE")
                        logger.info(f"-----------------------------------------------------------------------------------------------")
                        logger.info(f"New file: {file_path}")
                        
                        try:
                            # Copier le fichier vers le répertoire backup
                            logging.getLogger("COPY_FILE").info(f"Copy file: {file_path}")
                            copy_file(file_path, path_backup)

                            # Traiter le fichier
                            logging.getLogger("START_PROCESSING").info(f"Processing file: {file_path}")
                            kwargs = {
                                "file_path": file_path,
                                "config": config,
                            }
                            diagho_upload_file(**kwargs)

                            # Supprimer le fichier du répertoire 'input_data' après traitement
                            logging.getLogger("REMOVE_FILE").info(f"Remove file: {file_path}")
                            remove_file(file_path)

                        except Exception as e:
                            print(f"Failed to process file '{file_path}' - Erreur: {e}")

            # SI fichier modifié :
            if modified_files:
                for file in modified_files:
                    file_path = os.path.join(path_input, file)
                    
                    logger = logging.getLogger("MODIFIED_FILE")
                    logger.info(f"-----------------------------------------------------------------------------------------------")
                    logger.info(f"New file: {file_path}")
                    
                    try:
                        # Copier le fichier vers le répertoire backup
                        logging.getLogger("COPY_FILE").info(f"Copy file: {file_path}")
                        copy_file(file_path, path_backup)

                        # Traiter le fichier
                        logging.getLogger("START_PROCESSING").info(f"Processing file: {file_path}")
                        kwargs = {
                            "file_path": file_path,
                            "config": config,
                        }
                        diagho_upload_file(**kwargs)

                        # Supprimer le fichier du répertoire 'input_data' après traitement
                        logging.getLogger("REMOVE_FILE").info(f"Remove file: {file_path}")
                        remove_file(file_path)
                        
                    except Exception as e:
                        print(f"Failed to process modified file '{file_path}' - Erreur: {e}")

            # Mettre à jour la liste des fichiers pour la prochaine vérification
            previous_files = current_files

    except KeyboardInterrupt:
        print("Stop watching directory.")