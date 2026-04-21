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
            job.uploaded_files[filename] = BiofileUploader.upload(ctx, path, file_data)

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

    job.state = JobState.WAITING_PARSING
