import json
import shutil
from datetime import datetime
from uploader_v2.job.states import JobState
from uploader_v2.metadata.parser import parse_tsv_rows
from uploader_v2.metadata.builder import build_payload
from uploader_v2.metadata.validator import validate_payload

def step(job, ctx):
    files = list(ctx.metadata_dir.glob("*.tsv")) + list(ctx.metadata_dir.glob("*.json"))
    if not files:
        return

    path = files[0]
    print(f"file detected: {path}")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    try:
        if path.suffix == ".json":
            raw = json.loads(content)
        elif path.suffix == ".tsv":
            raw = build_payload(parse_tsv_rows(content))
        else:
            raise Exception(f"Incompatible file format: {path}")

        validated = validate_payload(raw)
        print(f"json validated")

        job.metadata_path = path
        job.metadata_json = validated
        job.expected_files = extract_expected_files(validated)
        job.state = JobState.WAITING_BIOFILES

        # Archive parsed metadata file
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        archived_name = f"{path.stem}_{timestamp}{path.suffix}"
        dst = ctx.archives_dir / archived_name
        shutil.move(str(path), str(dst))
        print(f"moved {path.stem} to {dst}")


    except Exception as e:
        print(e)
        job.last_error = str(e)
        job.state = JobState.FAILED

def extract_expected_files(metadata: dict) -> dict[str, str]:
    files = {
        f["filename"]: {
            "checksum": f["checksum"],
            "fileType": f["fileType"],
            "assembly": f["assembly"],
            "priority": f["priority"],
            # TODO: should be a get or create with run name instead of runId
            # fix on api/biofile_uploader as well
            # "run": f["run"],
        }
        for f in metadata["files"]
    }

    print(f"expected files: {files}")

    return files
