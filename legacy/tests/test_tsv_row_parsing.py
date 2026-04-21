from uploader_v2.models import TsvRow
import pytest


def test_minimal_row():
    row = TsvRow(
        filename="file1",
        checksum=None,
        file_type="SNV",
        assembly="GRCh38",
        sample="Sample1",
        bam_path=None,
        run=None,
        family_id="Family1",
        person_id="Person1",
        father_id=None,
        mother_id=None,
        sex=None,
        is_affected=None,
        first_name=None,
        last_name=None,
        date_of_birth=None,
        note=None,
        interpretation_title="Interp1",
        is_index=None,
        data_title=None,
        project="project1",
        assignee=None,
        priority=None,
        is_cohort=None,
        pretags=None
    )

    # assert row.file_type == "SNV"
    # assert row.is_cohort is False
    # assert row.priority == "normal"
