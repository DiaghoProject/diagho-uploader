import logging
from datetime import datetime, timezone

from ..states import JobState

logger = logging.getLogger(__name__)


def step(job, ctx):
    now = datetime.now(timezone.utc)

    if job.biofiles_wait_started is None:
        job.biofiles_wait_started = now

    timeout_minutes = ctx.biofile_timeout_minutes
    elapsed = (now - job.biofiles_wait_started).total_seconds() / 60
    if elapsed > timeout_minutes:
        missing = [f for f in job.expected_files if not (ctx.files_dir / f).exists()]
        logger.error("Biofile wait timeout after %.0f min — missing: %s", elapsed, missing)
        job.last_error = f"Timeout waiting for biofiles after {timeout_minutes} min: {missing}"
        job.state = JobState.FAILED
        return

    for filename in job.expected_files:
        if not (ctx.files_dir / filename).exists():
            logger.debug("Waiting for file: %s", filename)
            return

    job.state = JobState.UPLOADING_BIOFILES
