from dataclasses import dataclass
from pathlib import Path

from .api.client import ApiClient


@dataclass(frozen=True)
class Context:
    api: ApiClient

    metadata_dir: Path
    files_dir: Path
    archives_dir: Path

    # logger: object  # replace with logging.Logger if you want
