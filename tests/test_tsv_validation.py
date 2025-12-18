from uploader_v2.parser import parse_tsv_text
from uploader_v2.builders import build_payload
from uploader_v2.models import HardValidationError

TSV = """filename\tchecksum\tfile_type\tassembly\tsample\tbam_path\trun\tfamily_id\tperson_id\tfather_id\tmother_id\tsex\tis_affected\tfirst_name\tlast_name\tdate_of_birth\tnote\tinterpretation_title\tis_index\tdata_title\tproject\tassignee\tpriority\tis_cohort\tpretags
file1\ta368abdfb7780114f376d2f25f273307\tSNV\tGRCh38\tSample1\tpath/to/bam\trun name 1\tFamily1\tPerson1\tPerson3\tPerson2\tmale\t1\t\t\t\tnote example\tInterpretation1\t1\tSNV\tproject1\tuser1\t\t0\t[{\"tag_id\": 25, \"filter_id\": 63}, {\"tag_id\": 26, \"filter_id\": 68}, {\"tag_id\": 9, \"filter_id\": 42}]
file1\ta368abdfb7780114f376d2f25f273307\tSNV\tGRCh38\tSample2\tpath/to/bam\trun name 1\tFamily1\tPerson2\t\t\tfemale\t0\t\t\t\t\tInterpretation1\t0\tSNV\tproject1\tuser1\t\t0\t
file1\ta368abdfb7780114f376d2f25f273307\tSNV\tGRCh38\tSample3\tpath/to/bam\trun name 1\tFamily1\tPerson3\t\t\tmale\t0\t\t\t\t\tInterpretation1\t0\tSNV\tproject1\tuser1\t\t0\t
file2\tee78e54297c1c02ed93d92c7b18c18cb\tSNV\tGRCh38\tSample4\tpath/to/bam\trun name 1\tFamily2\tPerson4\tPerson5\t\tmale\t1\t\t\t\t\tInterpretation2\t1\tSNV\tproject2\tuser2\t\t1\t
file2\tee78e54297c1c02ed93d92c7b18c18cb\tSNV\tGRCh38\tSample5\tpath/to/bam\trun name 1\tFamily2\tPerson5\t\t\tmale\t0\t\t\t\t\tInterpretation2\t0\tSNV\tproject2\tuser2\t\t1\t
file3\tzelkfhzepokrfjkzlpejk,fz\tCNV\tGRCh38\tSample6\tpath/to/bam\trun name 1\tFamily2\tPerson4\t\t\tmale\t1\t\t\t\t\tInterpretation2\t1\tCNVtitle\tproject2\tuser2\t\t0\t
"""

def test_happy_path_parses_and_builds():
    rows = parse_tsv_text(TSV)
    payload = build_payload(rows)
    assert "families" in payload and "files" in payload and "interpretations" in payload
    assert len(payload["files"]) == 3
    interp1 = next((i for i in payload["interpretations"] if i["title"] == "Interpretation1"), None)
    assert interp1 is not None
    snv = next((d for d in interp1["datas"] if d["type"] == "SNV"), None)
    assert snv is not None and any(s["name"] == "Sample1" for s in snv["samples"])

def test_missing_index_raises():
    bad_tsv = TSV.replace("\\t1\\tSNV\\tproject1", "\\t0\\tSNV\\tproject1", 1)
    rows = parse_tsv_text(bad_tsv)
    try:
        build_payload(rows)
        assert False, "Expected HardValidationError due to missing index"
    except HardValidationError:
        pass

def test_invalid_pretags_drops_warns():
    bad = TSV.replace('{\"tag_id\": 25, \"filter_id\": 63}', '"not a json"')
    rows = parse_tsv_text(bad)
    payload = build_payload(rows)
    interp1 = next((i for i in payload["interpretations"] if i["title"] == "Interpretation1"), None)
    snv = next((d for d in interp1["datas"] if d["type"] == "SNV"), None)
    assert snv is not None
    assert snv.get("pretags") is None
