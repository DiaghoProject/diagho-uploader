from pathlib import Path
from unittest.mock import patch

import pytest

from uploader.job.model import IngestionJob
from uploader.runner import _done_body, _failed_body, build_context, validate_config

_VALID_CONFIG = {
    "metadata_dir": "/tmp/meta",
    "files_dir": "/tmp/files",
    "archives_dir": "/tmp/archives",
    "accessions": {"GRCh38": 2},
    "dedup_biofiles": False,
    "tabfiles_columns_index": {"1": "CHROM"},
    "tabfiles_zero_based": True,
    "diagho_api": {
        "username": "u",
        "password": "p",
        "url": "http://fake/api/v1/",
    },
}


# ---------------------------------------------------------------------------
# validate_config
# ---------------------------------------------------------------------------

def test_validate_config_valid_does_not_exit():
    validate_config(_VALID_CONFIG)  # must not raise


def test_validate_config_missing_top_level_key_exits():
    cfg = {k: v for k, v in _VALID_CONFIG.items() if k != "metadata_dir"}
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_validate_config_missing_diagho_api_exits():
    cfg = {k: v for k, v in _VALID_CONFIG.items() if k != "diagho_api"}
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_validate_config_diagho_api_not_dict_exits():
    cfg = {**_VALID_CONFIG, "diagho_api": "not-a-dict"}
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_validate_config_missing_api_url_exits():
    cfg = {**_VALID_CONFIG, "diagho_api": {"username": "u", "password": "p"}}
    with pytest.raises(SystemExit):
        validate_config(cfg)


# ---------------------------------------------------------------------------
# build_context
# ---------------------------------------------------------------------------

def test_build_context_paths():
    with patch("uploader.runner.ApiClient"):
        ctx = build_context(_VALID_CONFIG)
    assert ctx.metadata_dir == Path("/tmp/meta")
    assert ctx.files_dir == Path("/tmp/files")
    assert ctx.archives_dir == Path("/tmp/archives")


def test_build_context_biofile_timeout_defaults_to_60():
    with patch("uploader.runner.ApiClient"):
        ctx = build_context(_VALID_CONFIG)
    assert ctx.biofile_timeout_minutes == 60


def test_build_context_biofile_timeout_from_config():
    cfg = {**_VALID_CONFIG, "biofile_timeout_minutes": 120}
    with patch("uploader.runner.ApiClient"):
        ctx = build_context(cfg)
    assert ctx.biofile_timeout_minutes == 120


def test_build_context_passes_through_accessions_and_flags():
    with patch("uploader.runner.ApiClient"):
        ctx = build_context(_VALID_CONFIG)
    assert ctx.accessions == {"GRCh38": 2}
    assert ctx.dedup_biofiles is False
    assert ctx.tabfiles_zero_based is True


# ---------------------------------------------------------------------------
# _done_body
# ---------------------------------------------------------------------------

_METADATA_JSON = {
    "families": [
        {"identifier": "FAM1", "persons": [
            {"identifier": "P1", "sex": "male"},
            {"identifier": "P2", "sex": "female"},
        ]},
        {"identifier": "FAM2", "persons": [
            {"identifier": "P3", "sex": "male"},
        ]},
    ],
    "files": [],
    "interpretations": [
        {"title": "Interp A", "project": "proj-alpha", "assignee": "alice@lab.com", "indexCase": ["P1"], "datas": []},
        {"title": "Interp B", "project": "proj-beta", "assignee": None, "indexCase": ["P3"], "datas": []},
    ],
}


def test_done_body_includes_metadata_name():
    job = IngestionJob(job_id="test")
    job.metadata_path = Path("/archives/run001.tsv")
    job.uploaded_files = {"a.vcf.gz": "csum1", "b.vcf.gz": "csum2"}
    body = _done_body(job)
    assert "run001.tsv" in body
    assert "a.vcf.gz" in body
    assert "b.vcf.gz" in body


def test_done_body_no_metadata_path_shows_unknown():
    job = IngestionJob(job_id="test")
    job.uploaded_files = {}
    assert "unknown" in _done_body(job)


def test_done_body_shows_file_count():
    job = IngestionJob(job_id="test")
    job.metadata_path = Path("/archives/run001.tsv")
    job.uploaded_files = {"a.vcf.gz": "c1", "b.vcf.gz": "c2"}
    assert "2" in _done_body(job)


def test_done_body_summary_counts_with_metadata_json():
    job = IngestionJob(job_id="test")
    job.metadata_path = Path("/archives/run001.tsv")
    job.uploaded_files = {"a.vcf.gz": "c1"}
    job.metadata_json = _METADATA_JSON
    body = _done_body(job)
    assert "1 biofile" in body
    assert "2 families" in body
    assert "3 person" in body
    assert "2 interpretation" in body


def test_done_body_singular_family():
    job = IngestionJob(job_id="test")
    job.metadata_path = Path("/archives/run001.tsv")
    job.uploaded_files = {}
    job.metadata_json = {
        "families": [{"identifier": "FAM1", "persons": [{"identifier": "P1"}]}],
        "files": [],
        "interpretations": [],
    }
    assert "1 family" in _done_body(job)


def test_done_body_shows_interpretation_details():
    job = IngestionJob(job_id="test")
    job.metadata_path = Path("/archives/run001.tsv")
    job.uploaded_files = {}
    job.metadata_json = _METADATA_JSON
    body = _done_body(job)
    assert "Interp A" in body
    assert "proj-alpha" in body
    assert "alice@lab.com" in body
    assert "Interp B" in body
    assert "proj-beta" in body


def test_done_body_no_assignee_omits_assignee_label():
    job = IngestionJob(job_id="test")
    job.metadata_path = Path("/archives/run001.tsv")
    job.uploaded_files = {}
    job.metadata_json = {
        "families": [{"identifier": "FAM1", "persons": [{"identifier": "P1"}]}],
        "files": [],
        "interpretations": [
            {"title": "Solo", "project": "proj-x", "assignee": None, "indexCase": ["P1"], "datas": []},
        ],
    }
    body = _done_body(job)
    assert "Solo" in body
    assert "assignee" not in body


def test_done_body_without_metadata_json_shows_simple_summary():
    job = IngestionJob(job_id="test")
    job.metadata_path = Path("/archives/run001.tsv")
    job.uploaded_files = {"a.vcf.gz": "c1"}
    body = _done_body(job)
    assert "1 biofile" in body
    assert "families" not in body
    assert "Interpretations" not in body


# ---------------------------------------------------------------------------
# _failed_body
# ---------------------------------------------------------------------------

def test_failed_body_includes_state_and_error():
    job = IngestionJob(job_id="test")
    job.metadata_path = Path("/archives/run001.tsv")
    job.last_error = "checksum mismatch"
    body = _failed_body(job, "UPLOADING_BIOFILES")
    assert "UPLOADING_BIOFILES" in body
    assert "checksum mismatch" in body
    assert "run001.tsv" in body


def test_failed_body_no_error_shows_unknown():
    job = IngestionJob(job_id="test")
    body = _failed_body(job, "WAITING_BIOFILES")
    assert "unknown error" in body


def test_failed_body_no_metadata_shows_not_loaded():
    job = IngestionJob(job_id="test")
    assert "not loaded" in _failed_body(job, "WAITING_METADATA")
