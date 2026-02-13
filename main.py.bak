import sys
import argparse
import os
import yaml

from tabulated2json import *
from file_watcher import *
from utils.config_loader import *



# Load configuration            
def load_config(config_file):
    """Load configuration file."""
    try:
        with open(config_file, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error when loading configuration file: {e}", file=sys.stderr)
        sys.exit(1)

# Start file watcher
def run_file_watcher(config_file):
    """Command for starting the watcher."""
    # Load configuration file
    config = load_config(config_file)
    
    # Arguments
    kwargs = {
            "path_input": config.get("input_data", "."),
            "path_biofiles": config.get("input_biofiles", "."),
            "path_backup": config.get("backup_data"),
            "config": config,
            "config_file": os.path.abspath(config_file)
        }
    watch_directory(**kwargs)

def main():
    """
    Principal script.
    """
    # Load configuration file
    config_file = "config/config.yaml"
    config = load_config(config_file)
    
    # Arguments parser
    parser = argparse.ArgumentParser()

    # Define sub-commands
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command for 'start_file_watcher'
    subparsers.add_parser("start_file_watcher", help="Watch a directory.")

    try:
        # Get arguments
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        print(f"Arguments error: {e}", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Commands
    if args.command == "start_file_watcher":
        run_file_watcher(config_file)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
