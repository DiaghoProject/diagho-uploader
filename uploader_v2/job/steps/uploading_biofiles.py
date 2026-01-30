from uploader_v2.api.exceptions import AuthenticationError, ChecksumMismatchError, UploadError
from uploader_v2.job.states import JobState

def step(job, ctx):
    for filename, checksum in job.expected_files.items():
        if filename in job.uploaded_files:
            continue

        path = ctx.files_dir / filename

        try:
            remote_checksum = ctx.api.upload_file(path, checksum)
            job.uploaded_files[filename] = remote_checksum

        except AuthenticationError:
            ctx.logger.warning("Auth failed, will retry next loop")
            job.state = JobState.WAITING_FILES
            return
        except ChecksumMismatchError as e:
            ctx.logger.error(str(e))
            job.state = JobState.FAILED
            return
        except UploadError as e:
            ctx.logger.warning(str(e))
