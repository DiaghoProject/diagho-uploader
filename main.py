import argparse
import sys

import yaml

from uploader.runner import run_forever


def load_config(config_file: str) -> dict:
    try:
        with open(config_file) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Diagho genomic data uploader")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to config YAML (default: config/config.yaml)",
    )
    args = parser.parse_args()
    run_forever(load_config(args.config))


if __name__ == "__main__":
    main()
