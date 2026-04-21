import json
from pathlib import Path
from uploader_v2.context import Context


class BiofileUploader:
    def __init__(self, ctx: Context, file: Path, file_data: dict):
        self.ctx = ctx
        self.file = file
        self.checksum = file_data["checksum"]
        self.file_type = file_data["fileType"]
        self.assembly = file_data["assembly"]
        self.priority = file_data["priority"]
        # TODO: should be a get or create with run name instead of runId
        # self.run = file_data["run"]

    @classmethod
    def upload(cls, ctx: Context, file: Path, file_data: dict) -> str:
        return cls(ctx, file, file_data)._run()

    def _run(self) -> str:
        if self.file_type == "SNV":
            return self._upload_snv()
        elif self.file_type == "CNV":
            return self._upload_cnv()
        raise ValueError(f"File {self.file.stem} does not have a valid type: {self.file_type}")

    def _upload_snv(self) -> str:
        data = {
            "priority": self.priority,
            "accession": self.ctx.accessions[self.assembly],
            # TODO: uncomment with API update
            # "run": self.run,
            "dedup": self.ctx.dedup_biofiles,
        }
        print(f"uploading: {self.file.stem}")
        return self.ctx.api.upload_biofile("post_biofile_snv", data, self.file, self.checksum)

    def _upload_cnv(self) -> str:
        data = {
            "priority": self.priority,
            "assembly": self.assembly,
            # TODO: uncomment with API update
            # "run": self.run,
            "dedup": self.ctx.dedup_biofiles,
            "columnIndex": json.dumps(self.ctx.tabfiles_columns_index),
            "zeroBased": self.ctx.tabfiles_zero_based,
        }
        print(f"uploading: {self.file.stem}")
        return self.ctx.api.upload_biofile("post_biofile_cnv", data, self.file, self.checksum)
