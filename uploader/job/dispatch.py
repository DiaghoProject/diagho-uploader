from .states import JobState
from .steps import (
    waiting_metadata,
    waiting_biofiles,
    uploading_biofiles,
    waiting_parsing,
    posting_metadata,
)

DISPATCH = {
    JobState.WAITING_METADATA: waiting_metadata.step,
    JobState.WAITING_BIOFILES: waiting_biofiles.step,
    JobState.UPLOADING_BIOFILES: uploading_biofiles.step,
    JobState.WAITING_PARSING: waiting_parsing.step,
    JobState.POSTING_METADATA: posting_metadata.step,
    JobState.DONE: None,
    JobState.FAILED: None,
}

SLEEP_BY_STATE = {
    JobState.WAITING_METADATA: 30,
    JobState.WAITING_BIOFILES: 10,
    JobState.UPLOADING_BIOFILES: 10,
    JobState.WAITING_PARSING: 20,
}


def dispatch_step(job, ctx):
    step = DISPATCH.get(job.state)
    if step is not None:
        step(job, ctx)
