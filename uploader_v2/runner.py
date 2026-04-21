import logging
from pathlib import Path
from time import sleep

from uploader_v2.job.model import IngestionJob
from uploader_v2.job.dispatch import dispatch_step, SLEEP_BY_STATE
from uploader_v2.job.states import JobState
from uploader_v2.context import Context
from uploader_v2.infrastructure.api.client import ApiClient
from uploader_v2.utils.logger import setup_logger
from uploader_v2.utils.mailer import Mailer

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


def _done_body(job: IngestionJob) -> str:
    metadata = job.metadata_path.name if job.metadata_path else "unknown"
    biofiles = "\n".join(f"  - {f}" for f in job.uploaded_files)
    return (
        f"Ingestion completed successfully.\n\n"
        f"Metadata: {metadata}\n"
        f"Biofiles uploaded ({len(job.uploaded_files)}):\n{biofiles}"
    )


def _failed_body(job: IngestionJob, failed_from: str) -> str:
    metadata = job.metadata_path.name if job.metadata_path else "not loaded"
    return (
        f"Ingestion failed at state: {failed_from}\n\n"
        f"Error: {job.last_error or 'unknown error'}\n"
        f"Metadata: {metadata}"
    )


def run_forever(config: dict) -> None:
    setup_logger(config)
    logger.info("Uploader started")

    ctx    = build_context(config)
    mailer = Mailer(config)
    job    = IngestionJob(job_id="default")

    while True:
        prev_state = job.state
        dispatch_step(job, ctx)

        if job.state != prev_state:
            logger.info("State: %s → %s", prev_state.name, job.state.name)

        if job.state == JobState.DONE:
            logger.info("Job completed successfully")
            mailer.info(_done_body(job))
            job = IngestionJob(job_id="default")
            continue

        if job.state == JobState.FAILED:
            logger.error("Job failed: %s", job.last_error or "unknown error")
            mailer.alert(_failed_body(job, prev_state.name))
            job = IngestionJob(job_id="default")
            continue

        if job.state == prev_state:
            sleep(SLEEP_BY_STATE.get(job.state, 2))
