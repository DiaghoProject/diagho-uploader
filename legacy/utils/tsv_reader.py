# Parsing and aggregation implementation + basic tests (visible to user)
import csv, json, textwrap
from collections import defaultdict, OrderedDict
from pprint import pprint

TSV = """filename\tchecksum\tfile_type\tassembly\tsample\tbam_path\trun\tfamily_id\tperson_id\tfather_id\tmother_id\tsex\tis_affected\tfirst_name\tlast_name\tdate_of_birth\tnote\tinterpretation_title\tis_index\tdata_title\tproject\tassignee\tpriority\tis_cohort\tpretags
file1\ta368abdfb7780114f376d2f25f273307\tSNV\tGRCh38\tSample1\tpath/to/bam\trun name 1\tFamily1\tPerson1\tPerson3\tPerson2\tmale\t1\t\t\t\tnote example\tInterpretation1\t1\tSNV\tproject1\tuser1\t\t0\t[{\"tag_id\": 25, \"filter_id\": 63}, {\"tag_id\": 26, \"filter_id\": 68}, {\"tag_id\": 9, \"filter_id\": 42}]
file1\ta368abdfb7780114f376d2f25f273307\tSNV\tGRCh38\tSample2\tpath/to/bam\trun name 1\tFamily1\tPerson2\t\t\tfemale\t0\t\t\t\t\tInterpretation1\t0\tSNV\tproject1\tuser1\t\t0\t
file1\ta368abdfb7780114f376d2f25f273307\tSNV\tGRCh38\tSample3\tpath/to/bam\trun name 1\tFamily1\tPerson3\t\t\tmale\t0\t\t\t\t\tInterpretation1\t0\tSNV\tproject1\tuser1\t\t0\t
file2\tee78e54297c1c02ed93d92c7b18c18cb\tSNV\tGRCh38\tSample4\tpath/to/bam\trun name 1\tFamily2\tPerson4\tPerson5\t\tmale\t1\t\t\t\t\tInterpretation2\t1\tSNV\tproject2\tuser2\t\t1\t
file2\tee78e54297c1c02ed93d92c7b18c18cb\tSNV\tGRCh38\tSample5\tpath/to/bam\trun name 1\tFamily2\tPerson5\t\t\tmale\t0\t\t\t\t\tInterpretation2\t0\tSNV\tproject2\tuser2\t\t1\t
file3\tzelkfhzepokrfjkzlpejk,fz\tCNV\tGRCh38\tSample6\tpath/to/bam\trun name 1\tFamily2\tPerson4\t\t\tmale\t1\t\t\t\t\tInterpretation2\t1\tCNVtitle\tproject2\tuser2\t\t0\t
"""


def _parse_bool(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return v
    v = str(v).strip().lower()
    if v in ("1", "true", "yes", "y", "t"):
        return True
    if v in ("0", "false", "no", "n", "f"):
        return False
    return None


def _norm_checksum(ck):
    if ck is None:
        return None
    # take first token before any comma (handles weird CSV quirks)
    return str(ck).split(",")[0]


def parse_tsv_to_rows(tsv_text):
    """
    Parse TSV text into a list of normalized row dicts.
    Does lightweight coercion and pretags JSON parsing.
    """
    reader = csv.DictReader(tsv_text.splitlines(), delimiter="\t")
    rows = []
    for i, r in enumerate(reader, start=1):
        row = {k: (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
        # normalize booleans / ints where relevant
        row["is_affected"] = _parse_bool(row.get("is_affected"))
        row["is_index"] = _parse_bool(row.get("is_index"))
        row["is_cohort"] = _parse_bool(row.get("is_cohort"))
        # priority default
        row["priority"] = row.get("priority") or "normal"
        # file_type default SNV
        row["file_type"] = row.get("file_type") or "SNV"
        # checksum normalization
        row["checksum"] = _norm_checksum(row.get("checksum"))
        # pretags JSON parsing if present
        pretags_raw = row.get("pretags")
        if pretags_raw and pretags_raw.strip():
            try:
                row["pretags"] = json.loads(pretags_raw)
            except Exception:
                # try to coerce single quotes -> double quotes
                try:
                    row["pretags"] = json.loads(pretags_raw.replace("'", '"'))
                except Exception:
                    row["pretags"] = None
        else:
            row["pretags"] = None
        # keep line number for better error messages later
        row["_line"] = i + 1  # +1 for header (reader start)
        rows.append(row)
    return rows


def aggregate_families(rows):
    """
    rows: list of normalized dicts
    returns list of family dicts like in expected JSON
    """
    families = {}
    for r in rows:
        fam = r["family_id"]
        person_id = r["person_id"]
        if not fam or not person_id:
            continue
        if fam not in families:
            families[fam] = {"identifier": fam, "persons": {}}
        persons = families[fam]["persons"]
        if person_id not in persons:
            persons[person_id] = {
                "identifier": person_id
            }
        # optional attributes: sex, motherIdentifier, fatherIdentifier, comment
        if r.get("sex"):
            persons[person_id]["sex"] = r["sex"]
        if r.get("mother_id") or r.get("mother"):
            # handle different header names if present
            pass
        if r.get("mother_id") is not None:
            # nothing - prefer person-level mother_id if named that way
            pass
        # user headers: mother_id is 'mother_id' or 'mother_id' - in our TSV it's 'mother_id' spelled 'mother_id'? it's 'mother_id' absent.
        # In provided TSV header uses 'mother_id' indeed; but the user used 'mother_id' in description.
        # We check common keys:
        mother = r.get("mother_id") or r.get("mother") or r.get("motherIdentifier") or r.get("mother_id")
        father = r.get("father_id") or r.get("father") or r.get("fatherIdentifier") or r.get("father_id")
        if mother:
            persons[person_id]["motherIdentifier"] = mother
        if father:
            persons[person_id]["fatherIdentifier"] = father
        if r.get("note"):
            persons[person_id]["comment"] = r["note"]
    # convert to desired output: list of families, each with persons list
    out = []
    for famk, fv in families.items():
        persons_list = list(fv["persons"].values())
        out.append({"identifier": fv["identifier"], "persons": persons_list})
    return out


def aggregate_files(rows):
    """
    Aggregate by filename+checksum into file dicts with samples
    """
    files = OrderedDict()  # preserve encounter order
    for r in rows:
        fn = r["filename"]
        ck = r["checksum"]
        key = (fn, ck)
        if key not in files:
            files[key] = {"checksum": ck, "filename": fn, "samples": [], "run": r.get("run")}
        # each sample entry: name, person, bamPath
        sample_obj = {"name": r["sample"], "person": r["person_id"]}
        if r.get("bam_path"):
            sample_obj["bamPath"] = r["bam_path"]
        files[key]["samples"].append(sample_obj)
    return list(files.values())


def aggregate_interpretations(rows):
    """
    Build interpretations structure keyed by interpretation_title.
    Within each interpretation, datas keyed by (type,title)
    """
    interps = OrderedDict()
    for r in rows:
        title = r.get("interpretation_title") or "default"
        if title not in interps:
            interps[title] = {
                "title": title,
                "assignee": r.get("assignee"),
                "project": r.get("project"),
                "priority": r.get("priority") or "normal",
                "indexCase": None,
                "datas": OrderedDict()
            }
        interp = interps[title]
        # determine index case:
        if r.get("is_index") and interp["indexCase"] is None:
            interp["indexCase"] = r.get("person_id")
        # data bucket by file_type and data_title (title fallback to file_type)
        dtype = r.get("file_type") or "SNV"
        dtitle = r.get("data_title") or dtype
        dkey = (dtype, dtitle)
        if dkey not in interp["datas"]:
            interp["datas"][dkey] = {
                "type": dtype,
                "title": dtitle,
                "pretags": r.get("pretags"),
                "samples": [],
                "isCohort": bool(r.get("is_cohort"))
            }
        data = interp["datas"][dkey]
        # attach sample entry for this data
        samp = {
            "name": r.get("sample"),
            "isAffected": bool(r.get("is_affected")),
            "checksum": r.get("checksum")
        }
        data["samples"].append(samp)
        # if any row has pretags, keep them (assume same for the whole data bucket)
        if r.get("pretags"):
            data["pretags"] = r.get("pretags")
        # for is_cohort, once true keep true
        if r.get("is_cohort"):
            data["isCohort"] = True

    # convert datas OrderedDict to list and build final list
    out = []
    for title, info in interps.items():
        datas_list = []
        for d in info["datas"].values():
            datas_list.append(d)
        out.append({
            "indexCase": info["indexCase"],
            "assignee": info["assignee"],
            "project": info["project"],
            "title": info["title"],
            "priority": info["priority"],
            "datas": datas_list
        })
    return out


def build_payload(rows):
    return {
        "families": aggregate_families(rows),
        "files": aggregate_files(rows),
        "interpretations": aggregate_interpretations(rows)
    }


# --- Run parsing and show result ---
rows = parse_tsv_to_rows(TSV)
payload = build_payload(rows)

print("=== Parsed rows (first 2) ===")
pprint(rows[:2])
print("\n=== Final payload ===")
print(json.dumps(payload, indent=2))

# --- Basic assertions to validate structure against expectations ---
# These are not exhaustive unit tests but sanity checks you can expand into pytest later.
assert len(payload["files"]) == 3, f"expected 3 files, got {len(payload['files'])}"
assert any(f["filename"] == "file1" for f in payload["files"]), "file1 missing"
# check interpretation1 has sample1 and correct checksum
interp1 = next((i for i in payload["interpretations"] if i["title"] == "Interpretation1"), None)
assert interp1 is not None, "Interpretation1 missing"
snv_data = next((d for d in interp1["datas"] if d["type"] == "SNV"), None)
assert snv_data is not None, "SNV data missing in Interpretation1"
s1 = next((s for s in snv_data["samples"] if s["name"] == "Sample1"), None)
assert s1 is not None and s1["checksum"] == "a368abdfb7780114f376d2f25f273307", "Sample1 checksum mismatch"

# check interpretation2 has CNV data and cohort flags
interp2 = next((i for i in payload["interpretations"] if i["title"] == "Interpretation2"), None)
assert interp2 is not None, "Interpretation2 missing"
cnv_data = next((d for d in interp2["datas"] if d["type"] == "CNV"), None)
assert cnv_data is not None, "CNV data missing in Interpretation2"
assert any(s["name"] == "Sample6" for s in cnv_data["samples"]), "Sample6 missing in CNV data"

print("\nAll sanity checks passed. You can turn these into pytest tests easily.")
