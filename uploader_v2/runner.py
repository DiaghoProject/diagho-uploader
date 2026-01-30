from .job.model import IngestionJob
from .job.states import JobState
from .job.dispatch import dispatch_step
from .context import Context
from .api.client import ApiClient
from time import sleep

def build_context(config):
    api = ApiClient(config.api)

    return Context(
        api=api,
        metadata_dir=config.metadata_dir,
        files_dir=config.files_dir,
        poll_interval=config.poll_interval,
        logger=config.logger,
    )
def run_forever(config):
    job = IngestionJob(job_id="default")
    ctx = build_context(config)

    while True:
        dispatch_step(job, ctx)
        sleep(config.poll_interval)
