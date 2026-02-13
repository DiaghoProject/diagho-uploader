from uploader_v2.runner import run_forever
# from .config import load_config
import yaml
import sys

def load_config(config_file):
    """Load configuration file."""
    try:
        with open(config_file, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error when loading configuration file: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    config = load_config("config/config.yaml")
    run_forever(config)

if __name__ == "__main__":
    main()