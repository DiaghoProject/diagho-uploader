import pytest

from tests.conftest import SAMPLE_TSV
from uploader.metadata.parser import parse_tsv_rows
from uploader.metadata.builder import build_payload
from uploader.metadata.validator import validate_payload
from uploader.metadata.tsv_schema import TsvRow, HardValidationError, Priority


# ---------------------------------------------------------------------------
# TsvRow field validators
# ---------------------------------------------------------------------------

def _minimal_row(**overrides) -> TsvRow:
    defaults = dict(
        filename="f.vcf.gz",
        checksum="aaaabbbbccccddddeeeeffffaaaabbbb",
        assembly="GRCh38",
        sample="S001",
        family_id="FAM001",
        person_id="P001",
        interpretation_title="Interp001",
        project="proj01",
    )
    return TsvRow(**{**defaults, **overrides})


def test_empty_assignee_becomes_none():
    assert _minimal_row(assignee="").assignee is None
    assert _minimal_row(assignee=None).assignee is None


def test_non_empty_assignee_preserved():
    assert _minimal_row(assignee="analyst01").assignee == "analyst01"


def test_blank_priority_defaults_to_normal():
    assert _minimal_row(priority="").priority == Priority.normal
    assert _minimal_row(priority=None).priority == Priority.normal


def test_legacy_int_priority_maps():
    assert _minimal_row(priority="0").priority == Priority.low
    assert _minimal_row(priority="1").priority == Priority.normal
    assert _minimal_row(priority="2").priority == Priority.high
    assert _minimal_row(priority="3").priority == Priority.highest


def test_invalid_priority_falls_back_to_normal():
    assert _minimal_row(priority="urgent").priority == Priority.normal


def test_bool_fields_parse_truthy():
    row = _minimal_row(is_index="true", is_cohort="yes")
    assert row.is_index is True
    assert row.is_cohort is True


def test_bool_fields_parse_falsy():
    row = _minimal_row(is_index="false", is_cohort="no")
    assert row.is_index is False
    assert row.is_cohort is False


def test_pretags_valid_json():
    row = _minimal_row(pretags='[{"tag_id": 1, "filter_id": 2}]')
    assert row.pretags is not None
    assert row.pretags[0].tag_id == 1


def test_pretags_single_quote_repair():
    row = _minimal_row(pretags="[{'tag_id': 1, 'filter_id': 2}]")
    assert row.pretags is not None
    assert row.pretags[0].filter_id == 2


def test_pretags_garbage_becomes_none():
    assert _minimal_row(pretags="not json at all").pretags is None


def test_pretags_empty_becomes_none():
    assert _minimal_row(pretags="").pretags is None
    assert _minimal_row(pretags=None).pretags is None


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parser_returns_correct_row_count():
    rows = parse_tsv_rows(SAMPLE_TSV)
    assert len(rows) == 4


def test_parser_assigns_line_numbers():
    rows = parse_tsv_rows(SAMPLE_TSV)
    assert rows[0]._line == 2
    assert rows[3]._line == 5


def test_parser_invalid_row_raises():
    # file_type maps to DataType enum — an unrecognised value triggers validation error
    bad_tsv = SAMPLE_TSV.replace("\tSNV\t", "\tINVALID_TYPE\t", 1)
    with pytest.raises(ValueError, match="TSV parse error"):
        parse_tsv_rows(bad_tsv)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def test_build_payload_top_level_keys():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    assert set(payload.keys()) == {"families", "files", "interpretations"}


def test_build_payload_file_count():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    assert len(payload["files"]) == 2


def test_build_payload_family_count():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    assert len(payload["families"]) == 2


def test_build_payload_family_members():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    fam001 = next(f for f in payload["families"] if f["identifier"] == "FAM001")
    assert len(fam001["persons"]) == 3


def test_build_payload_parent_links():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    fam001 = next(f for f in payload["families"] if f["identifier"] == "FAM001")
    index_person = next(p for p in fam001["persons"] if p["identifier"] == "PERSON001")
    assert index_person["fatherIdentifier"] == "PERSON003"
    assert index_person["motherIdentifier"] == "PERSON002"


def test_build_payload_interpretation_index_case():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    interp1 = next(i for i in payload["interpretations"] if i["title"] == "Interp001")
    assert interp1["indexCase"] == "PERSON001"


def test_build_payload_pretags_on_index_row():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    interp1 = next(i for i in payload["interpretations"] if i["title"] == "Interp001")
    snv_data = next(d for d in interp1["datas"] if d["type"] == "SNV")
    assert snv_data["pretags"] is not None
    assert snv_data["pretags"][0]["tag_id"] == 1


def test_build_payload_missing_index_raises():
    no_index_tsv = SAMPLE_TSV.replace(
        "Interp001\t1\tSNV",  # first row (index case)
        "Interp001\t0\tSNV",
        1,
    )
    rows = parse_tsv_rows(no_index_tsv)
    with pytest.raises(HardValidationError, match="no index case"):
        build_payload(rows)


def test_build_payload_invalid_pretags_drops_gracefully():
    bad_tsv = SAMPLE_TSV.replace(
        '[{"tag_id": 1, "filter_id": 2}]',
        "definitely not json",
    )
    rows = parse_tsv_rows(bad_tsv)
    payload = build_payload(rows)
    interp1 = next(i for i in payload["interpretations"] if i["title"] == "Interp001")
    snv_data = next(d for d in interp1["datas"] if d["type"] == "SNV")
    assert snv_data.get("pretags") is None


# ---------------------------------------------------------------------------
# Full pipeline: parse → build → validate
# ---------------------------------------------------------------------------

def test_full_pipeline_produces_valid_payload():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    validated = validate_payload(payload)
    assert "families" in validated
    assert "files" in validated
    assert "interpretations" in validated


def test_full_pipeline_no_none_values():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    validated = validate_payload(payload)
    # exclude_none=True must strip all None fields
    def _has_none(obj):
        if isinstance(obj, dict):
            return any(v is None or _has_none(v) for v in obj.values())
        if isinstance(obj, list):
            return any(_has_none(i) for i in obj)
        return False
    assert not _has_none(validated)


def test_full_pipeline_enum_values_are_strings():
    rows = parse_tsv_rows(SAMPLE_TSV)
    payload = build_payload(rows)
    validated = validate_payload(payload)
    file_ = validated["files"][0]
    assert isinstance(file_["fileType"], str)
    interp = validated["interpretations"][0]
    assert isinstance(interp["priority"], str)
