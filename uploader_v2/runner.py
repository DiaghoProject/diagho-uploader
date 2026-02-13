from uploader_v2.job.model import IngestionJob
# from uploader_v2.job.states import JobState
from uploader_v2.job.dispatch import dispatch_step
from uploader_v2.context import Context
from uploader_v2.api.client import ApiClient
from time import sleep
from pathlib import Path

def build_context(config):
    api = ApiClient(config)

    return Context(
        api=api,
        metadata_dir=Path(config["metadata_dir"]),
        files_dir=Path(config["files_dir"]),
        archives_dir=Path(config["archives_dir"]),
        # poll_interval=config.poll_interval,
        # logger=config.logger,
    )

def run_forever(config):
    job = IngestionJob(job_id="default")
    ctx = build_context(config)

    while True:
        dispatch_step(job, ctx)
        # sleep(config.poll_interval)
