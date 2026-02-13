from uploader_v2.job.states import JobState
from uploader_v2.job.steps import (
    metadata_ready,
    waiting_biofiles,
    uploading_biofiles
)

DISPATCH = {
    JobState.WAITING_METADATA: metadata_ready.step,
    JobState.WAITING_BIOFILES: waiting_biofiles.step,
    JobState.UPLOADING_BIOFILES: uploading_biofiles.step,
    JobState.WAITING_PARSING: None,
    JobState.POSTING_METADATA: None,
    JobState.DONE: None,
    JobState.FAILED: None
}

def dispatch_step(job, ctx):
    DISPATCH[job.state](job, ctx)
