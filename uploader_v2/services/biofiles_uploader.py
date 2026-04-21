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
        # fix on steps/metadata_ready as well
        # self.run = file_data["run"]
        self.upload_strategy()

    def upload_strategy(self):
        if (self.file_type == "SNV"):
            self.upload_snv_file()
        elif (self.file_type == "CNV"):
            self.upload_cnv_file()
        else:
            raise ValueError(f"File {self.file.stem} does not have a valid type: {self.file_type}")

    def upload_snv_file(self):
        accession = self.ctx.accessions[self.assembly]
        dedup = self.ctx.dedup_biofiles

        data = {
            "priority": self.priority.value,
            "accession": accession,
            # TODO: uncomment with API update
            # "run": self.run,
            "dedup": dedup,
        }

        print(f"uploading: {self.file.stem}")

        return self.ctx.api.upload_biofile("post_biofile_snv", data, self.file, self.checksum)

    def upload_cnv_file(self):
        dedup = self.ctx.dedup_biofiles
        tabfiles_columns_index=self.ctx.tabfiles_columns_index
        tabfiles_zero_based=self.ctx.tabfiles_zero_based

        data = {
            "priority": self.priority.value,
            "assembly": self.assembly.value,
            # TODO: uncomment with API update
            # "run": self.run,
            "dedup": dedup,
            "columnIndex": tabfiles_columns_index,
            "zeroBased": tabfiles_zero_based,
        }

        print(f"uploading: {self.file.stem}")

        return self.ctx.api.upload_biofile("post_biofile_cnv", data, self.file, self.checksum)