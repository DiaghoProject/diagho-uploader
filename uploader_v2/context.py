from dataclasses import dataclass
from pathlib import Path

from .infrastructure.api.client import ApiClient


@dataclass(frozen=True)
class Context:
    api: ApiClient

    metadata_dir: Path
    files_dir: Path
    archives_dir: Path

    accessions: dict[str, int]
    tabfiles_columns_index: dict[str, str]
    tabfiles_zero_based: bool = True
    dedup_biofiles: bool = False

    # logger: object  # replace with logging.Logger if you want
