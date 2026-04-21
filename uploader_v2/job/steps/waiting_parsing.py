import logging

from ..states import JobState
from uploader_v2.infrastructure.api.exceptions import ApiError

logger = logging.getLogger(__name__)

_SUCCESS = "success"
_FAILURE = "failure"


def step(job, ctx):
    for filename, checksum in job.uploaded_files.items():
        try:
            status = ctx.api.get_biofile_loading_status(checksum)
        except ApiError as e:
            logger.warning("Could not poll status for %s: %s — will retry", filename, e)
            return

        logger.debug("%s loading status: %s", filename, status)

        if status.lower() == _FAILURE:
            logger.error("Biofile '%s' failed to parse (status: %s)", filename, status)
            job.last_error = f"Biofile '{filename}' failed to parse (status: {status})"
            job.state = JobState.FAILED
            return

        if status.lower() != _SUCCESS:
            logger.info("%s still loading (status: %s)", filename, status)
            return

    logger.info("All biofiles parsed successfully")
    job.state = JobState.POSTING_METADATA
