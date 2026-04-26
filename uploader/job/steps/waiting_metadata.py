import json
import logging
import shutil
from datetime import datetime

from ..states import JobState
from uploader.metadata.parser import parse_tsv_rows
from uploader.metadata.builder import build_payload
from uploader.metadata.validator import validate_payload

logger = logging.getLogger(__name__)


def step(job, ctx):
    files = list(ctx.metadata_dir.glob("*.tsv")) + list(ctx.metadata_dir.glob("*.json"))
    if not files:
        return

    path = files[0]  # process one file per cycle; any remaining files will be picked up in subsequent passes
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job.job_id = f"{path.stem}_{timestamp}"
    logger.info("[%s] Metadata file detected: %s", job.job_id, path.name)
    content = path.read_text(encoding="utf-8")

    try:
        if path.suffix == ".json":
            raw = json.loads(content)
        elif path.suffix == ".tsv":
            raw = build_payload(parse_tsv_rows(content))
        else:
            raise ValueError(f"Unsupported metadata format: {path.suffix}")

        validated = validate_payload(raw)
        logger.debug("[%s] Validated payload: %s", job.job_id, validated)

        expected = _extract_expected_files(validated)
        logger.info(
            "[%s] %d biofile(s) expected: %s",
            job.job_id,
            len(expected),
            list(expected.keys()),
        )

        job.metadata_path = path
        job.metadata_json = validated
        job.expected_files = expected
        job.state = JobState.WAITING_BIOFILES

        dst = ctx.archives_dir / f"{path.stem}_{timestamp}{path.suffix}"
        shutil.move(str(path), str(dst))
        logger.info("[%s] Metadata archived to %s", job.job_id, dst.name)

    except Exception as e:
        logger.error("[%s] Metadata processing failed: %s", job.job_id, e)
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
