from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from tests.conftest import SAMPLE_TSV
from uploader.job.model import IngestionJob
from uploader.job.states import JobState
from uploader.job.steps import (
    waiting_metadata,
    waiting_biofiles,
    uploading_biofiles,
    waiting_parsing,
    posting_metadata,
)
from uploader.infrastructure.api.exceptions import (
    ApiError,
    AuthenticationError,
    ChecksumMismatchError,
    MaxAuthRetriesError,
    UploadError,
)

_EXPECTED_FILES = {
    "snv001.vcf.gz": {
        "checksum": "aaaabbbbccccddddeeeeffffaaaabbbb",
        "fileType": "SNV",
        "assembly": "GRCh38",
        "priority": "normal",
    }
}


# ---------------------------------------------------------------------------
# waiting_metadata
# ---------------------------------------------------------------------------

def test_waiting_metadata_no_files_stays(mock_ctx):
    job = IngestionJob(job_id="init")
    waiting_metadata.step(job, mock_ctx)
    assert job.state == JobState.WAITING_METADATA


def test_waiting_metadata_valid_tsv_transitions(mock_ctx):
    (mock_ctx.metadata_dir / "run001.tsv").write_text(SAMPLE_TSV, encoding="utf-8")
    job = IngestionJob(job_id="init")
    waiting_metadata.step(job, mock_ctx)
    assert job.state == JobState.WAITING_BIOFILES


def test_waiting_metadata_sets_meaningful_job_id(mock_ctx):
    (mock_ctx.metadata_dir / "run001.tsv").write_text(SAMPLE_TSV, encoding="utf-8")
    job = IngestionJob(job_id="init")
    waiting_metadata.step(job, mock_ctx)
    assert job.job_id.startswith("run001_")


def test_waiting_metadata_populates_expected_files(mock_ctx):
    (mock_ctx.metadata_dir / "run001.tsv").write_text(SAMPLE_TSV, encoding="utf-8")
    job = IngestionJob(job_id="init")
    waiting_metadata.step(job, mock_ctx)
    assert "snv001.vcf.gz" in job.expected_files
    assert "cnv002.tsv" in job.expected_files


def test_waiting_metadata_archives_tsv(mock_ctx):
    (mock_ctx.metadata_dir / "run001.tsv").write_text(SAMPLE_TSV, encoding="utf-8")
    job = IngestionJob(job_id="init")
    waiting_metadata.step(job, mock_ctx)
    remaining = list(mock_ctx.metadata_dir.glob("*.tsv"))
    archived  = list(mock_ctx.archives_dir.glob("*.tsv"))
    assert len(remaining) == 0
    assert len(archived) == 1


def test_waiting_metadata_invalid_tsv_fails(mock_ctx):
    # file_type enum violation causes a parse error → step transitions to FAILED
    bad_content = SAMPLE_TSV.replace("\tSNV\t", "\tINVALID_TYPE\t", 1)
    (mock_ctx.metadata_dir / "bad.tsv").write_text(bad_content, encoding="utf-8")
    job = IngestionJob(job_id="init")
    waiting_metadata.step(job, mock_ctx)
    assert job.state == JobState.FAILED
    assert job.last_error is not None


# ---------------------------------------------------------------------------
# waiting_biofiles
# ---------------------------------------------------------------------------

def test_waiting_biofiles_all_present_transitions(mock_ctx):
    (mock_ctx.files_dir / "snv001.vcf.gz").write_bytes(b"fake")
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES
    waiting_biofiles.step(job, mock_ctx)
    assert job.state == JobState.UPLOADING_BIOFILES


def test_waiting_biofiles_missing_file_stays(mock_ctx):
    job = IngestionJob(job_id="test")
    job.state = JobState.WAITING_BIOFILES
    job.expected_files = _EXPECTED_FILES
    waiting_biofiles.step(job, mock_ctx)
    assert job.state == JobState.WAITING_BIOFILES


def test_waiting_biofiles_sets_start_timestamp(mock_ctx):
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES
    assert job.biofiles_wait_started is None
    waiting_biofiles.step(job, mock_ctx)
    assert job.biofiles_wait_started is not None


def test_waiting_biofiles_timeout_fails(mock_ctx):
    mock_ctx.biofile_timeout_minutes = 60
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES
    job.biofiles_wait_started = datetime.now(timezone.utc) - timedelta(hours=2)
    waiting_biofiles.step(job, mock_ctx)
    assert job.state == JobState.FAILED
    assert "Timeout" in job.last_error


# ---------------------------------------------------------------------------
# uploading_biofiles
# ---------------------------------------------------------------------------

def test_uploading_biofiles_success_transitions(mock_ctx):
    fake_file = mock_ctx.files_dir / "snv001.vcf.gz"
    fake_file.write_bytes(b"fake")
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES

    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload",
               return_value="aaaabbbbccccddddeeeeffffaaaabbbb"):
        uploading_biofiles.step(job, mock_ctx)

    assert job.state == JobState.WAITING_PARSING
    assert "snv001.vcf.gz" in job.uploaded_files


def test_uploading_biofiles_archives_file(mock_ctx):
    fake_file = mock_ctx.files_dir / "snv001.vcf.gz"
    fake_file.write_bytes(b"fake")
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES

    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload",
               return_value="aaaabbbbccccddddeeeeffffaaaabbbb"):
        uploading_biofiles.step(job, mock_ctx)

    assert not fake_file.exists()
    assert (mock_ctx.archives_dir / "snv001.vcf.gz").exists()


def test_uploading_biofiles_skips_already_uploaded(mock_ctx):
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES
    job.uploaded_files = {"snv001.vcf.gz": "aaaabbbbccccddddeeeeffffaaaabbbb"}

    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload") as mock_upload:
        uploading_biofiles.step(job, mock_ctx)

    mock_upload.assert_not_called()
    assert job.state == JobState.WAITING_PARSING


def test_uploading_biofiles_upload_error_increments_attempts(mock_ctx):
    job = IngestionJob(job_id="test")
    job.state = JobState.UPLOADING_BIOFILES
    job.expected_files = _EXPECTED_FILES

    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload",
               side_effect=UploadError("snv001.vcf.gz")):
        uploading_biofiles.step(job, mock_ctx)

    assert job.state == JobState.UPLOADING_BIOFILES
    assert job.upload_attempts["snv001.vcf.gz"] == 1


def test_uploading_biofiles_max_attempts_fails(mock_ctx):
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES
    job.upload_attempts = {"snv001.vcf.gz": 4}

    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload",
               side_effect=UploadError("snv001.vcf.gz")):
        uploading_biofiles.step(job, mock_ctx)

    assert job.state == JobState.FAILED


def test_uploading_biofiles_checksum_mismatch_fails(mock_ctx):
    (mock_ctx.files_dir / "snv001.vcf.gz").write_bytes(b"fake")
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES

    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload",
               side_effect=ChecksumMismatchError("snv001.vcf.gz", "expected", "got")):
        uploading_biofiles.step(job, mock_ctx)

    assert job.state == JobState.FAILED


def test_uploading_biofiles_auth_error_stays_uploading(mock_ctx):
    job = IngestionJob(job_id="test")
    job.state = JobState.UPLOADING_BIOFILES
    job.expected_files = _EXPECTED_FILES

    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload",
               side_effect=AuthenticationError("token expired")):
        uploading_biofiles.step(job, mock_ctx)

    assert job.state == JobState.UPLOADING_BIOFILES


def test_uploading_biofiles_max_auth_retries_fails(mock_ctx):
    job = IngestionJob(job_id="test")
    job.expected_files = _EXPECTED_FILES

    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload",
               side_effect=MaxAuthRetriesError(7)):
        uploading_biofiles.step(job, mock_ctx)

    assert job.state == JobState.FAILED
    assert job.last_error is not None


_TWO_FILES = {
    "snv001.vcf.gz": {
        "checksum": "aaaabbbbccccddddeeeeffffaaaabbbb",
        "fileType": "SNV",
        "assembly": "GRCh38",
        "priority": "normal",
    },
    "cnv002.tsv": {
        "checksum": "11112222333344445555666677778888",
        "fileType": "CNV",
        "assembly": "GRCh38",
        "priority": "normal",
    },
}


def test_uploading_biofiles_auth_failure_preserves_already_uploaded(mock_ctx):
    (mock_ctx.files_dir / "snv001.vcf.gz").write_bytes(b"fake")
    (mock_ctx.files_dir / "cnv002.tsv").write_bytes(b"fake")
    job = IngestionJob(job_id="test")
    job.state = JobState.UPLOADING_BIOFILES
    job.expected_files = _TWO_FILES

    # first file uploads, second triggers auth failure
    with patch("uploader.job.steps.uploading_biofiles.BiofileUploader.upload",
               side_effect=["aaaabbbbccccddddeeeeffffaaaabbbb", AuthenticationError("expired")]):
        uploading_biofiles.step(job, mock_ctx)

    assert "snv001.vcf.gz" in job.uploaded_files
    assert job.state == JobState.UPLOADING_BIOFILES  # not stuck, not failed


# ---------------------------------------------------------------------------
# waiting_parsing
# ---------------------------------------------------------------------------

def test_waiting_parsing_all_success_transitions(mock_ctx):
    job = IngestionJob(job_id="test")
    job.uploaded_files = {"snv001.vcf.gz": "aaaabbbbccccddddeeeeffffaaaabbbb"}
    mock_ctx.api.get_biofile_loading_status.return_value = "success"

    waiting_parsing.step(job, mock_ctx)

    assert job.state == JobState.POSTING_METADATA


def test_waiting_parsing_pending_stays(mock_ctx):
    job = IngestionJob(job_id="test")
    job.state = JobState.WAITING_PARSING
    job.uploaded_files = {"snv001.vcf.gz": "aaaabbbbccccddddeeeeffffaaaabbbb"}
    mock_ctx.api.get_biofile_loading_status.return_value = "loading"

    waiting_parsing.step(job, mock_ctx)

    assert job.state == JobState.WAITING_PARSING


def test_waiting_parsing_failure_fails(mock_ctx):
    job = IngestionJob(job_id="test")
    job.state = JobState.WAITING_PARSING
    job.uploaded_files = {"snv001.vcf.gz": "aaaabbbbccccddddeeeeffffaaaabbbb"}
    mock_ctx.api.get_biofile_loading_status.return_value = "failure"

    waiting_parsing.step(job, mock_ctx)

    assert job.state == JobState.FAILED
    assert "snv001.vcf.gz" in job.last_error


def test_waiting_parsing_api_error_stays(mock_ctx):
    job = IngestionJob(job_id="test")
    job.state = JobState.WAITING_PARSING
    job.uploaded_files = {"snv001.vcf.gz": "aaaabbbbccccddddeeeeffffaaaabbbb"}
    mock_ctx.api.get_biofile_loading_status.side_effect = ApiError("timeout")

    waiting_parsing.step(job, mock_ctx)

    assert job.state == JobState.WAITING_PARSING


# ---------------------------------------------------------------------------
# posting_metadata
# ---------------------------------------------------------------------------

def test_posting_metadata_success_done(mock_ctx):
    job = IngestionJob(job_id="test")
    job.metadata_json = {"families": [], "files": [], "interpretations": []}
    mock_ctx.api.post_metadata.return_value = None

    posting_metadata.step(job, mock_ctx)

    assert job.state == JobState.DONE


def test_posting_metadata_api_error_fails(mock_ctx):
    job = IngestionJob(job_id="test")
    job.metadata_json = {}
    mock_ctx.api.post_metadata.side_effect = ApiError("server error")

    posting_metadata.step(job, mock_ctx)

    assert job.state == JobState.FAILED
    assert job.last_error is not None
