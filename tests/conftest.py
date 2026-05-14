import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Synthetic TSV: 2 files (SNV + CNV), 2 families, 2 interpretations.
# All identifiers are clearly fake — no real patient data.
SAMPLE_TSV = (
    "filename\tchecksum\tfile_type\tassembly\tsample\tbam_path\trun\t"
    "family_id\tperson_id\tfather_id\tmother_id\tsex\t"
    "first_name\tlast_name\tdate_of_birth\tnote\tinterpretation_title\t"
    "is_index\tis_dataset_index\tdata_title\tproject\tassignee\tpriority\tis_cohort\tpretags\n"

    'snv001.vcf.gz\taaaabbbbccccddddeeeeffffaaaabbbb\tSNV\tGRCh38\tSAMPLE001\t\t\t'
    'FAM001\tPERSON001\tPERSON003\tPERSON002\tmale\t\t\t\t\t'
    'Interp001\t1\t1\tSNV\tproject01\tanalyst01\tnormal\t0\t'
    '[{"tag_id": 1, "filter_id": 2}]\n'

    'snv001.vcf.gz\taaaabbbbccccddddeeeeffffaaaabbbb\tSNV\tGRCh38\tSAMPLE002\t\t\t'
    'FAM001\tPERSON002\t\t\tfemale\t\t\t\t\t'
    'Interp001\t0\t\tSNV\tproject01\tanalyst01\tnormal\t0\t\n'

    'snv001.vcf.gz\taaaabbbbccccddddeeeeffffaaaabbbb\tSNV\tGRCh38\tSAMPLE003\t\t\t'
    'FAM001\tPERSON003\t\t\tmale\t\t\t\t\t'
    'Interp001\t0\t\tSNV\tproject01\tanalyst01\tnormal\t0\t\n'

    'cnv002.tsv\t11112222333344445555666677778888\tCNV\tGRCh38\tSAMPLE004\t\t\t'
    'FAM002\tPERSON004\t\t\tmale\t\t\t\t\t'
    'Interp002\t1\t\tCNV\tproject01\tanalyst02\thigh\t0\t\n'
)


# Same structure as SAMPLE_TSV but with interpretation columns left blank.
NO_INTERP_TSV = (
    "filename\tchecksum\tfile_type\tassembly\tsample\tbam_path\trun\t"
    "family_id\tperson_id\tfather_id\tmother_id\tsex\t"
    "first_name\tlast_name\tdate_of_birth\tnote\tinterpretation_title\t"
    "is_index\tis_dataset_index\tdata_title\tproject\tassignee\tpriority\tis_cohort\tpretags\n"

    'snv001.vcf.gz\taaaabbbbccccddddeeeeffffaaaabbbb\tSNV\tGRCh38\tSAMPLE001\t\t\t'
    'FAM001\tPERSON001\tPERSON003\tPERSON002\tmale\t\t\t\t\t'
    '\t\t\t\t\t\tnormal\t0\t\n'

    'snv001.vcf.gz\taaaabbbbccccddddeeeeffffaaaabbbb\tSNV\tGRCh38\tSAMPLE002\t\t\t'
    'FAM001\tPERSON002\t\t\tfemale\t\t\t\t\t'
    '\t\t\t\t\t\tnormal\t0\t\n'
)


@pytest.fixture
def sample_tsv():
    return SAMPLE_TSV


@pytest.fixture
def mock_ctx(tmp_path):
    ctx = MagicMock()
    ctx.metadata_dir = tmp_path / "metadata"
    ctx.files_dir    = tmp_path / "files"
    ctx.archives_dir = tmp_path / "archives"
    for d in (ctx.metadata_dir, ctx.files_dir, ctx.archives_dir):
        d.mkdir()
    ctx.api.get_biofile_checksum_status.return_value = None
    ctx.accessions             = {"GRCh37": 1, "GRCh38": 2}
    ctx.tabfiles_columns_index = {"1": "CHROM", "2": "START", "3": "END"}
    ctx.tabfiles_zero_based    = True
    ctx.dedup_biofiles         = False
    ctx.biofile_timeout_minutes = 60
    return ctx
