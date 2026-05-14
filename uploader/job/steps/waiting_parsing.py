import logging

from ..states import JobState
from uploader.infrastructure.api.exceptions import ApiError

logger = logging.getLogger(__name__)

_SUCCESS = "success"
_FAILURE = "failure"


def step(job, ctx):
    total = len(job.uploaded_files)

    for filename, checksum in job.uploaded_files.items():
        if filename in job.parsed_files:
            continue

        try:
            status = ctx.api.get_biofile_loading_status(checksum)
        except ApiError as e:
            logger.warning("Could not poll status for %s: %s — will retry", filename, e)
            return

        if status.lower() == _FAILURE:
            logger.error("Biofile '%s' failed to parse (status: %s)", filename, status)
            job.last_error = f"Biofile '{filename}' failed to parse (status: {status})"
            job.state = JobState.FAILED
            return

        if status.lower() == _SUCCESS:
            job.parsed_files.add(filename)
            logger.info("Parsed: %s (%d/%d)", filename, len(job.parsed_files), total)
        else:
            logger.debug(
                "Waiting for parsing: %d/%d done, %s still %s",
                len(job.parsed_files), total, filename, status,
            )
            return

    logger.info("All %d biofiles parsed successfully", total)
    job.state = JobState.POSTING_METADATA
