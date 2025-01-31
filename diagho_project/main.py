import sys
import argparse
import time
import os
import yaml
import shutil

from diagho_create_inputs.parser import *
from diagho_uploader.file_watcher import *


# Load configuration            
def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Create JSON file
def run_create_inputs(input_file, output_file):
    """
    Céation du JSON à partir du TSV.
    """
    # create_inputs(input_file, output_file)
    
    print(f"Création du fichier JSON '{output_file}' à partir de '{input_file}'")

# Start file watcher
def run_file_watcher(**kwargs):
    """
    Uploader les fichiers dans l'application.
    """
    path_input = kwargs.get("path_input")
    path_backup = kwargs.get("path_backup")
    path_biofiles = kwargs.get("path_biofiles")
    config = kwargs.get("config")
    
    watch_directory(path_input, path_backup, path_biofiles, config)
    
    print(f"Surveillance du répertoire {path_input}")


# main
def main():
    # Parser d'arguments
    parser = argparse.ArgumentParser()

    # Définir les sous-commandes
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sous-commande pour 'create_inputs'
    create_parser = subparsers.add_parser("create_inputs", help="Créer un fichier JSON à partir d'un fichier TSV")
    create_parser.add_argument("--input_file", help="Chemin vers le fichier TSV d'entrée")
    create_parser.add_argument("--output_file", help="Chemin vers le fichier JSON de sortie")

    # Sous-commande pour 'start_file_watcher'
    watch_parser = subparsers.add_parser("start_file_watcher", help="Surveiller un répertoire pour des fichiers JSON")

    # Analyser les arguments
    args = parser.parse_args()

    # Exécuter la fonction correspondante en fonction de la sous-commande passée en argument
    if args.command == "create_inputs":
        try:
            
            input_file = args.input_file
            output_file = args.output_file
            # Vérifier que les arguments nécessaires sont fournis
            if not input_file or not output_file:
                print("Erreur: Vous devez fournir à la fois 'input_file' et 'output_file'.")
                sys.exit(1)
            
            run_create_inputs(input_file, output_file)
            
        except Exception as e:
            print(f"Erreur lors de la création des inputs : {e}")
            sys.exit(1)
            
        
        
    elif args.command == "start_file_watcher":
        
        # Load configuration file
        config = load_config("config/config.yaml")
    
        # Args
        kwargs = {
            "path_input": config.get("input_data", "."),
            "path_biofiles": config.get("input_biofiles", "."),
            "path_backup": config.get("backup_data"),
            "config": config,
        }
        run_file_watcher(**kwargs)
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
