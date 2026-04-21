import logging
import shutil

from ..states import JobState
from uploader_v2.services.biofiles_uploader import BiofileUploader
from uploader_v2.infrastructure.api.exceptions import AuthenticationError, ChecksumMismatchError, UploadError
from uploader_v2.context import Context

logger = logging.getLogger(__name__)


def step(job, ctx: Context):
    for filename, file_data in job.expected_files.items():
        if filename in job.uploaded_files:
            continue

        path = ctx.files_dir / filename
        logger.info("Uploading %s (%s)", filename, file_data["fileType"])

        try:
            checksum = BiofileUploader.upload(ctx, path, file_data)
            job.uploaded_files[filename] = checksum
            logger.info("Uploaded %s — checksum: %s", filename, checksum)
        except AuthenticationError:
            logger.warning("Authentication failed during upload, will retry")
            job.state = JobState.WAITING_BIOFILES
            return
        except ChecksumMismatchError as e:
            logger.error("Checksum mismatch for %s: %s", filename, e)
            job.last_error = str(e)
            job.state = JobState.FAILED
            return
        except UploadError as e:
            logger.warning("Upload error for %s: %s — will retry", filename, e)
            job.last_error = str(e)
            return

        dst = ctx.archives_dir / filename
        if dst.exists():
            dst.unlink()
        shutil.move(str(path), str(dst))
        logger.info("Archived %s", filename)

    job.state = JobState.WAITING_PARSING
