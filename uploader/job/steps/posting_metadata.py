import logging

from ..states import JobState
from uploader.infrastructure.api.exceptions import ApiError

logger = logging.getLogger(__name__)


def step(job, ctx):
    logger.info("Posting metadata configuration")
    try:
        ctx.api.post_metadata(job.metadata_json)
    except ApiError as e:
        logger.error("Metadata post failed: %s", e)
        job.last_error = str(e)
        job.state = JobState.FAILED
        return

    logger.info("Metadata posted successfully")
    job.state = JobState.DONE
