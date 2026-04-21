from uploader_v2.job.states import JobState
from uploader_v2.infrastructure.api.exceptions import ApiError

_SUCCESS = "success"
_FAILURE = "failure"


def step(job, ctx):
    for filename, checksum in job.uploaded_files.items():
        try:
            status = ctx.api.get_biofile_loading_status(checksum)
        except ApiError as e:
            print(f"Error polling status for {filename}: {e}")
            return  # transient error, retry next loop

        if status.lower() == _FAILURE:
            job.last_error = f"Biofile '{filename}' failed to parse (status: {status})"
            job.state = JobState.FAILED
            return

        if status.lower() != _SUCCESS:
            return  # at least one file still loading, stay in WAITING_PARSING

    job.state = JobState.POSTING_METADATA
