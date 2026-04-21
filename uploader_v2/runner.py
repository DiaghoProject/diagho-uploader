import logging
from pathlib import Path
from time import sleep

from uploader_v2.job.model import IngestionJob
from uploader_v2.job.dispatch import dispatch_step, SLEEP_BY_STATE
from uploader_v2.job.states import JobState
from uploader_v2.context import Context
from uploader_v2.infrastructure.api.client import ApiClient
from uploader_v2.utils.logger import setup_logger

logger = logging.getLogger(__name__)


def build_context(config: dict) -> Context:
    return Context(
        api=ApiClient(config),
        metadata_dir=Path(config["metadata_dir"]),
        files_dir=Path(config["files_dir"]),
        archives_dir=Path(config["archives_dir"]),
        accessions=config["accessions"],
        dedup_biofiles=config["dedup_biofiles"],
        tabfiles_columns_index=config["tabfiles_columns_index"],
        tabfiles_zero_based=config["tabfiles_zero_based"],
    )


def run_forever(config: dict) -> None:
    setup_logger(config)
    logger.info("Uploader started")

    ctx = build_context(config)
    job = IngestionJob(job_id="default")

    while True:
        prev_state = job.state
        dispatch_step(job, ctx)

        if job.state != prev_state:
            logger.info("State: %s → %s", prev_state.name, job.state.name)

        if job.state == JobState.DONE:
            logger.info("Job completed successfully")
            job = IngestionJob(job_id="default")
            continue

        if job.state == JobState.FAILED:
            logger.error("Job failed: %s", job.last_error or "unknown error")
            job = IngestionJob(job_id="default")
            continue

        if job.state == prev_state:
            sleep(SLEEP_BY_STATE.get(job.state, 2))
