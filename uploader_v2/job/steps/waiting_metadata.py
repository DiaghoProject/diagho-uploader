import json
import shutil
from datetime import datetime

from ..states import JobState
from uploader_v2.metadata.parser import parse_tsv_rows
from uploader_v2.metadata.builder import build_payload
from uploader_v2.metadata.validator import validate_payload


def step(job, ctx):
    files = list(ctx.metadata_dir.glob("*.tsv")) + list(ctx.metadata_dir.glob("*.json"))
    if not files:
        return

    path = files[0]
    content = path.read_text(encoding="utf-8")

    try:
        if path.suffix == ".json":
            raw = json.loads(content)
        elif path.suffix == ".tsv":
            raw = build_payload(parse_tsv_rows(content))
        else:
            raise ValueError(f"Unsupported metadata format: {path.suffix}")

        validated = validate_payload(raw)

        job.metadata_path = path
        job.metadata_json = validated
        job.expected_files = _extract_expected_files(validated)
        job.state = JobState.WAITING_BIOFILES

        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        shutil.move(str(path), str(ctx.archives_dir / f"{path.stem}_{timestamp}{path.suffix}"))

    except Exception as e:
        job.last_error = str(e)
        job.state = JobState.FAILED


def _extract_expected_files(metadata: dict) -> dict:
    return {
        f["filename"]: {
            "checksum": f["checksum"],
            "fileType": f["fileType"],
            "assembly": f["assembly"],
            "priority": f["priority"],
        }
        for f in metadata["files"]
    }
