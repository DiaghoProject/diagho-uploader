import argparse
import json
import logging
import signal
import sys
from pathlib import Path
from time import sleep

import yaml

from uploader.runner import run_forever
from uploader.metadata.parser import parse_tsv_rows
from uploader.metadata.builder import build_payload
from uploader.metadata.validator import validate_payload


def load_config(config_file: str) -> dict:
    try:
        with open(config_file) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)


def parse_only(config: dict) -> None:
    logging.disable(logging.CRITICAL)

    metadata_dir = Path(config["metadata_dir"])
    _stop = False

    def _on_signal(s, f):
        nonlocal _stop
        _stop = True

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    while not _stop:
        files = list(metadata_dir.glob("*.tsv")) + list(metadata_dir.glob("*.json"))
        if files:
            path = files[0]
            content = path.read_text(encoding="utf-8")
            try:
                if path.suffix == ".json":
                    raw = json.loads(content)
                elif path.suffix == ".tsv":
                    raw = build_payload(parse_tsv_rows(content))
                else:
                    print(f"Unsupported format: {path.suffix}", file=sys.stderr)
                    sys.exit(1)
                validated = validate_payload(raw)
                print(json.dumps(validated, indent=2))
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
            return
        sleep(2)


def main():
    parser = argparse.ArgumentParser(description="Diagho genomic data uploader")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to config YAML (default: config/config.yaml)",
    )
    parser.add_argument(
        "--parse",
        action="store_true",
        help="Wait for a TSV/JSON in metadata_dir, print the validated JSON payload, exit",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    if args.parse:
        parse_only(config)
    else:
        run_forever(config)


if __name__ == "__main__":
    main()
