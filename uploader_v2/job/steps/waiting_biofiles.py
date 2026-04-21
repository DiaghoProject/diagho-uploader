import logging

from ..states import JobState

logger = logging.getLogger(__name__)


def step(job, ctx):
    for filename in job.expected_files:
        if not (ctx.files_dir / filename).exists():
            logger.debug("Waiting for file: %s", filename)
            return

    job.state = JobState.UPLOADING_BIOFILES
