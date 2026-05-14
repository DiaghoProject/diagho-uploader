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
from uploader.metadata.payload_schema import MetadataPayload
from uploader.utils.logger import setup_logger
from uploader.utils.mailer import Mailer

logger = logging.getLogger(__name__)

_shutdown = False

_REQUIRED_KEYS = [
    "metadata_dir",
    "files_dir",
    "archives_dir",
    "accessions",
    "dedup_biofiles",
    "tabfiles_columns_index",
    "tabfiles_zero_based",
]
_REQUIRED_API_KEYS = ["username", "password", "url"]


def validate_config(config: dict) -> None:
    missing = [k for k in _REQUIRED_KEYS if k not in config]
    api_cfg = config.get("diagho_api")
    if not isinstance(api_cfg, dict):
        missing.append("diagho_api")
    else:
        missing += [f"diagho_api.{k}" for k in _REQUIRED_API_KEYS if k not in api_cfg]
    if missing:
        logger.error(
            "Missing required config keys:\n%s",
            "\n".join(f"  - {k}" for k in missing),
        )
        sys.exit(1)


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


# Mail content
def _done_body(job: IngestionJob) -> str:
    metadata_name = job.metadata_path.name if job.metadata_path else "unknown"
    n_biofiles = len(job.uploaded_files)

    payload = MetadataPayload.model_validate(job.metadata_json) if job.metadata_json else None

    if payload:
        n_families = len(payload.families)
        n_persons = sum(len(f.persons) for f in payload.families)
        n_interps = len(payload.interpretations)
        summary = (
            f"Handled {n_biofiles} biofile(s), regarding "
            f"{n_families} famil{'y' if n_families == 1 else 'ies'} with {n_persons} person(s) "
            f"and created {n_interps} interpretation(s)."
        )
    else:
        summary = f"Handled {n_biofiles} biofile(s)."

    parts = [
        "Ingestion completed successfully.",
        f"Metadata file: {metadata_name}",
        summary,
        "",
        f"Biofiles uploaded ({n_biofiles}):",
        *[f"  - {f}" for f in job.uploaded_files],
    ]

    if payload and payload.interpretations:
        parts += ["", f"Interpretations created ({n_interps}):"]
        for interp in payload.interpretations:
            assignee = f" (assignee: {interp.assignee})" if interp.assignee else ""
            parts.append(f"  - {interp.title} [project: {interp.project}]{assignee}")

    return "\n".join(parts)


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
    validate_config(config)
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
            sleep(SLEEP_BY_STATE.get(job.state, 30))

    logger.info("Uploader stopped")
