from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .states import JobState


@dataclass
class IngestionJob:
    job_id: str

    state: JobState = JobState.WAITING_METADATA

    metadata_path: Optional[Path] = None
    metadata_json: Optional[dict] = None

    expected_files: Dict[str, Dict[str, str]] = field(default_factory=dict)
    uploaded_files: Dict[str, str] = field(default_factory=dict)
    upload_attempts: Dict[str, int] = field(default_factory=dict)
    parsed_files: set[str] = field(default_factory=set)

    biofiles_wait_started: Optional[datetime] = None

    last_error: Optional[str] = None
