import time
import os
import yaml
import shutil
from datetime import datetime

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
        logging.StreamHandler()                                         # Afficher les logs sur la console (pour log final)
    ]
)


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
    print(f"Watching directory: {path_input}")

    try:
        while True:
            time.sleep(5)  # Toutes les 5 secondes
            current_files = list_files(path_input)

            # Comparer les fichiers créés et modifiés
            new_files = set(current_files) - set(previous_files)
            modified_files = {f for f in current_files if f in previous_files and current_files[f] != previous_files[f]}

            if new_files:
                for file in new_files:
                    if file.endswith(".json"): # prendre en compte uniquement les JSON
                        file_path = os.path.join(path_input, file)
                        print(f"\nNew file - Processing file: {file_path}")
                        logging.getLogger("NEW_FILE").info(f"New file: {file_path}")
                        try:
                            # Copier le fichier vers le répertoire backup
                            logging.getLogger("START_PROCESSING").info(f"Copy file: {file_path}")
                            copy_file(file_path, path_backup)

                            # Traiter le fichier
                            logging.getLogger("START_PROCESSING").info(f"Processing file: {file_path}")
                            # diagho_process_file(file_path, config)

                            # Supprimer le fichier du répertoire 'input_data' après traitement
                            logging.getLogger("START_PROCESSING").info(f"Remove file: {file_path}")
                            remove_file(file_path)

                        except Exception as e:
                            print(f"Failed to process file '{file_path}' - Erreur: {e}")

            if modified_files:
                for file in modified_files:
                    file_path = os.path.join(path_input, file)
                    print(f"\nFile modified - Processing file: {file_path}")
                    logging.getLogger("MODIFIED_FILE").info(f"New file: {file_path}")
                    try:
                        # Copier le fichier vers le répertoire backup
                        logging.getLogger("START_PROCESSING").info(f"Copy file: {file_path}")
                        copy_file(file_path, path_backup)

                        # Traiter le fichier
                        logging.getLogger("START_PROCESSING").info(f"Processing file: {file_path}")
                        # diagho_process_file(file_path, config)

                        # Supprimer le fichier du répertoire 'input_data' après traitement
                        logging.getLogger("START_PROCESSING").info(f"Remove file: {file_path}")
                        remove_file(file_path)
                        
                    except Exception as e:
                        print(f"Failed to process modified file '{file_path}' - Erreur: {e}")

            # Mettre à jour la liste des fichiers pour la prochaine vérification
            previous_files = current_files

    except KeyboardInterrupt:
        print("Stop watching directory.")