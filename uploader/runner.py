import logging
import signal
import sys
from pathlib import Path
from time import sleep

from uploader.job.model import IngestionJob
from uploader.job.dispatch import dispatch_step, SLEEP_BY_STATE
from uploader.job.states import JobState
from uploader.context import Context
from uploader.infrastructure.api.client import ApiClient
from uploader.infrastructure.api.exceptions import ApiError
from uploader.utils.logger import setup_logger
from uploader.utils.mailer import Mailer

logger = logging.getLogger(__name__)

_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    logger.info("Shutdown signal received, will stop after current step")
    _shutdown = True


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
        biofile_timeout_minutes=config.get("biofile_timeout_minutes", 60),
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
    global _shutdown
    _shutdown = False
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    setup_logger(config)
    logger.info("Uploader started")

    ctx    = build_context(config)
    mailer = Mailer(config)

    try:
        ctx.api.healthcheck()
        logger.info("API healthcheck passed")
    except ApiError as e:
        logger.error("API unreachable at startup: %s", e)
        sys.exit(1)

    job = IngestionJob(job_id="init")

    while not _shutdown:
        prev_state = job.state
        dispatch_step(job, ctx)

        if job.state != prev_state:
            logger.info("[%s] State: %s → %s", job.job_id, prev_state.name, job.state.name)

        if job.state == JobState.DONE:
            logger.info("[%s] Job completed successfully", job.job_id)
            mailer.info(_done_body(job))
            job = IngestionJob(job_id="init")
            continue

        if job.state == JobState.FAILED:
            logger.error("[%s] Job failed: %s", job.job_id, job.last_error or "unknown error")
            mailer.alert(_failed_body(job, prev_state.name))
            job = IngestionJob(job_id="init")
            continue

        if job.state == prev_state:
            sleep(SLEEP_BY_STATE.get(job.state, 2))

    logger.info("Uploader stopped")
