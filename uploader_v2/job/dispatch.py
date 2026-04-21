from uploader_v2.job.states import JobState
from uploader_v2.job.steps import (
    metadata_ready,
    waiting_biofiles,
    uploading_biofiles,
    waiting_parsing,
    posting_metadata,
)

DISPATCH = {
    JobState.WAITING_METADATA: metadata_ready.step,
    JobState.WAITING_BIOFILES: waiting_biofiles.step,
    JobState.UPLOADING_BIOFILES: uploading_biofiles.step,
    JobState.WAITING_PARSING: waiting_parsing.step,
    JobState.POSTING_METADATA: posting_metadata.step,
    JobState.DONE: None,
    JobState.FAILED: None
}

SLEEP_BY_STATE = {
    JobState.WAITING_METADATA: 20,
    JobState.WAITING_BIOFILES: 10,
    JobState.WAITING_PARSING: 20,
    JobState.POSTING_METADATA: 0
}

def dispatch_step(job, ctx):
    step = DISPATCH.get(job.state)
    if step is not None:
        step(job, ctx)
