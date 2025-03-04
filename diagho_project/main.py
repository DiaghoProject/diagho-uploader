import sys
import argparse
import time
import os
import yaml
import shutil

from diagho_create_inputs.parser import *
from diagho_uploader.file_watcher import *
from common.config_loader import *



# Load configuration            
def load_config(config_file):
    """Chargement du fichier de configuration."""
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Create JSON file
def run_create_inputs(input_file, output_file):
    """Création du JSON à partir du TSV."""
    create_json_files(input_file, output_file)

# Start file watcher
def run_file_watcher(**kwargs):
    """Uploader les fichiers dans l'application."""
    kwargs = {
            "path_input": kwargs.get("path_input"),
            "path_biofiles": kwargs.get("path_biofiles"),
            "path_backup": kwargs.get("path_backup"),
            "config": kwargs.get("config"),
            "config_file": kwargs.get("config_file")
        }
    # path_input = kwargs.get("path_input")
    # path_backup = kwargs.get("path_backup")
    # path_biofiles = kwargs.get("path_biofiles")
    # config = kwargs.get("config")
    # config_file = kwargs.get("config_file")

    watch_directory(**kwargs)

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
    
    # Create_inputs : ne sert plus ?
    # TODO: à virer
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
            print(f"Erreur lors de la création des fichiers: {e}")
            sys.exit(1)
    
    # Start file_watcher
    elif args.command == "start_file_watcher":
        
        # Load configuration file
        config_file = "config/config.yaml"
        config = load_config(config_file)
    
        # Args
        kwargs = {
            "path_input": config.get("input_data", "."),
            "path_biofiles": config.get("input_biofiles", "."),
            "path_backup": config.get("backup_data"),
            "config": config,
            "config_file": os.path.abspath(config_file)
        }
        run_file_watcher(**kwargs)
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
