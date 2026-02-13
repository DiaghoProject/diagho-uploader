from uploader_v2.job.states import JobState

def step(job, ctx):
    files_dir = ctx.files_dir

    for filename in job.expected_files:
        path = files_dir / filename
        if not path.exists():
            # ctx.logger.debug(f"Waiting for file {filename}")
            return  # stay in WAITING_FILES

    job.state = JobState.UPLOADING_BIOFILES
