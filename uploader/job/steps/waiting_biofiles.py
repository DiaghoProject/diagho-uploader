import logging
from datetime import datetime, timezone

from uploader.infrastructure.api.exceptions import ApiError
from ..states import JobState

logger = logging.getLogger(__name__)


def step(job, ctx):
    now = datetime.now(timezone.utc)

    if job.biofiles_wait_started is None:
        job.biofiles_wait_started = now

    # Pre-check app: mark files whose checksum is already loaded so upload can be skipped
    for filename, file_data in job.expected_files.items():
        if filename in job.uploaded_files:
            continue
        checksum = file_data["checksum"]
        try:
            status = ctx.api.get_biofile_checksum_status(checksum)
        except ApiError as e:
            logger.warning("Could not query app for %s: %s — will check locally", filename, e)
            continue
        if status is not None:
            logger.info("Biofile %s already uploaded in Diagho (status: %s)", filename, status)
            job.uploaded_files[filename] = checksum
            if status.lower() == "success":
                job.parsed_files.add(filename)

    # All files accounted for → skip upload and parsing wait entirely
    if all(f in job.uploaded_files for f in job.expected_files):
        logger.info("All biofiles already uploaded — skipping to posting metadata")
        job.state = JobState.POSTING_METADATA
        return

    # Some files still need uploading — enforce timeout
    timeout_minutes = ctx.biofile_timeout_minutes
    elapsed = (now - job.biofiles_wait_started).total_seconds() / 60
    if elapsed > timeout_minutes:
        missing = [
            f for f in job.expected_files
            if f not in job.uploaded_files and not (ctx.files_dir / f).exists()
        ]
        logger.error("Biofile wait timeout after %.0f min — missing: %s", elapsed, missing)
        job.last_error = f"Timeout waiting for biofiles after {timeout_minutes} min: {missing}"
        job.state = JobState.FAILED
        return

    # Wait for remaining files to appear locally
    for filename in job.expected_files:
        if filename in job.uploaded_files:
            continue
        if not (ctx.files_dir / filename).exists():
            logger.debug("Waiting for file: %s", filename)
            return

    job.state = JobState.UPLOADING_BIOFILES
