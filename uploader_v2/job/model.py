from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional
from .states import JobState

@dataclass
class IngestionJob:
    job_id: str

    state: JobState = JobState.WAITING_METADATA

    metadata_path: Optional[Path] = None
    metadata_json: Optional[dict] = None

    expected_files: Dict[str, str] = field(default_factory=dict)
    uploaded_files: Dict[str, str] = field(default_factory=dict)

    last_error: Optional[str] = None
