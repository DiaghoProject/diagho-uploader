from uploader_v2.job.states import JobState
from uploader_v2.metadata.parser import build_from_tsv
from uploader_v2.metadata.validator import validate_payload


# def step(job, ctx):
#     path = job.metadata_path

#     try:
#         if path.suffix == ".tsv":
#             raw = build_from_tsv(path)
#         else:
#             raw = ctx.json_loader(path)

#         validated = validate_payload(raw)

#         job.metadata_json = validated
#         job.expected_files = extract_expected_files(validated)
#         job.state = JobState.WAITING_BIOFILES

#     except Exception as e:
#         job.last_error = str(e)
#         job.state = JobState.FAILED

def step(job, ctx):
    files = list(ctx.metadata_dir.glob("*.tsv")) + list(ctx.metadata_dir.glob("*.json"))
    if not files:
        return

    path = files[0]

    try:
        if path.suffix == ".tsv":
            raw = build_from_tsv(path)
        else:
            raw = ctx.json_loader(path)

        validated = validate_payload(raw)

        job.metadata_path = path
        job.metadata_json = validated
        job.expected_files = extract_expected_files(validated)
        job.state = JobState.WAITING_FILES

    except Exception as e:
        job.last_error = str(e)
        job.state = JobState.FAILED

def extract_expected_files(metadata: dict) -> dict[str, str]:
    files = {}

    for f in metadata["files"]:
        filename = f["filename"]
        checksum = f["checksum"]

        # TODO: fix that
        # if filename in files and files[filename] != checksum:
        #     ctx.logger.warning(
        #         f"Same filename with different checksum: {filename}"
        #     )

        files[filename] = checksum

    return files
