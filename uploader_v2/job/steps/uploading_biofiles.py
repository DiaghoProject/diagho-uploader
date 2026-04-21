import shutil

from ..states import JobState
from uploader_v2.services.biofiles_uploader import BiofileUploader
from uploader_v2.infrastructure.api.exceptions import AuthenticationError, ChecksumMismatchError, UploadError
from uploader_v2.context import Context


def step(job, ctx: Context):
    for filename, file_data in job.expected_files.items():
        if filename in job.uploaded_files:
            continue

        path = ctx.files_dir / filename

        try:
            job.uploaded_files[filename] = BiofileUploader.upload(ctx, path, file_data)
        except AuthenticationError:
            job.state = JobState.WAITING_BIOFILES
            return
        except ChecksumMismatchError as e:
            job.last_error = str(e)
            job.state = JobState.FAILED
            return
        except UploadError as e:
            job.last_error = str(e)
            return  # stay in UPLOADING_BIOFILES, retry next loop

        dst = ctx.archives_dir / filename
        if dst.exists():
            dst.unlink()
        shutil.move(str(path), str(dst))

    job.state = JobState.WAITING_PARSING
