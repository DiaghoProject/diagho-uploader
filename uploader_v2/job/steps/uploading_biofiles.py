from uploader_v2.services.biofiles_uploader import BiofileUploader
from uploader_v2.infrastructure.api.exceptions import AuthenticationError, ChecksumMismatchError, UploadError
from uploader_v2.context import Context
from uploader_v2.job.states import JobState

def step(job, ctx: Context):
    print("starting upload")
    for filename, file_data in job.expected_files.items():
        if filename in job.uploaded_files:
            continue

        path = ctx.files_dir / filename

        try:
            # remote_checksum = ctx.api.upload_file(path, file_data)
            uploader = BiofileUploader(ctx, path, file_data)
            job.uploaded_files[filename] = uploader.remote_checksum

        except AuthenticationError:
            # ctx.logger.warning("Auth failed, will retry next loop")
            job.state = JobState.WAITING_BIOFILES
            return
        except ChecksumMismatchError as e:
            # ctx.logger.error(str(e))
            job.state = JobState.FAILED
            return
        except UploadError as e:
            print(e)
            # ctx.logger.warning(str(e))
