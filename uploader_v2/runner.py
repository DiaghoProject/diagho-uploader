from uploader_v2.job.model import IngestionJob
from uploader_v2.job.dispatch import dispatch_step, SLEEP_BY_STATE
from uploader_v2.context import Context
from uploader_v2.infrastructure.api.client import ApiClient
from time import sleep
from pathlib import Path

def build_context(config):
    api = ApiClient(config)

    return Context(
        api=api,
        metadata_dir=Path(config["metadata_dir"]),
        files_dir=Path(config["files_dir"]),
        archives_dir=Path(config["archives_dir"]),
        accessions=config["accessions"],
        tabfiles_columns_index=config["tabfiles_columns_index"],
        dedup_biofiles=config["dedup_biofiles"],
        tabfiles_columns_index=config["tabfiles_columns_index"],
        tabfiles_zero_based=config["tabfiles_zero_based"],
        # logger=config.logger,
    )

def run_forever(config):
    job = IngestionJob(job_id="default")
    ctx = build_context(config)

    while True:
        prev_state = job.state
        dispatch_step(job, ctx)

        if job.state == prev_state:
            sleep_time = SLEEP_BY_STATE.get(job.state, 2)
            sleep(sleep_time)
