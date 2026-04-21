from ..states import JobState
from uploader_v2.infrastructure.api.exceptions import ApiError


def step(job, ctx):
    try:
        ctx.api.post_metadata(job.metadata_json)
    except ApiError as e:
        job.last_error = str(e)
        job.state = JobState.FAILED
        return

    job.state = JobState.DONE
