from ..states import JobState


def step(job, ctx):
    for filename in job.expected_files:
        if not (ctx.files_dir / filename).exists():
            return

    job.state = JobState.UPLOADING_BIOFILES
