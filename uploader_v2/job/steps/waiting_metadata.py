import json
import logging
import shutil
from datetime import datetime

from ..states import JobState
from uploader_v2.metadata.parser import parse_tsv_rows
from uploader_v2.metadata.builder import build_payload
from uploader_v2.metadata.validator import validate_payload

logger = logging.getLogger(__name__)


def step(job, ctx):
    files = list(ctx.metadata_dir.glob("*.tsv")) + list(ctx.metadata_dir.glob("*.json"))
    if not files:
        return

    path = files[0]
    logger.info("Metadata file detected: %s", path.name)
    content = path.read_text(encoding="utf-8")

    try:
        if path.suffix == ".json":
            raw = json.loads(content)
        elif path.suffix == ".tsv":
            raw = build_payload(parse_tsv_rows(content))
        else:
            raise ValueError(f"Unsupported metadata format: {path.suffix}")

        validated = validate_payload(raw)
        logger.debug("Validated payload: %s", validated)

        expected = _extract_expected_files(validated)
        logger.info(
            "%d biofile(s) expected: %s",
            len(expected),
            list(expected.keys()),
        )

        job.metadata_path = path
        job.metadata_json = validated
        job.expected_files = expected
        job.state = JobState.WAITING_BIOFILES

        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        dst = ctx.archives_dir / f"{path.stem}_{timestamp}{path.suffix}"
        shutil.move(str(path), str(dst))
        logger.info("Metadata archived to %s", dst.name)

    except Exception as e:
        logger.error("Metadata processing failed: %s", e)
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
