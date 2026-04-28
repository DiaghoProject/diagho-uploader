from collections import OrderedDict
from typing import List, Dict, Any, Tuple

from .tsv_schema import TsvRow, HardValidationError, PretagItem


def ensure_single_index(interp_rows: List[TsvRow], title: str):
    indexes = list(set((r.person_id, r.is_index) for r in interp_rows if r.is_index))
    if len(indexes) > 1:
        raise HardValidationError(f"Interpretation '{title}' has multiple index cases: {indexes}")
    if len(indexes) == 0:
        raise HardValidationError(f"Interpretation '{title}' has no index case (required)")


def build_families(rows: List[TsvRow]) -> List[Dict[str, Any]]:
    families: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        if not r.family_id or not r.person_id:
            raise HardValidationError(f"Missing family_id or person_id at line {r._line}")
        fam = families.setdefault(r.family_id, {"identifier": r.family_id, "persons": OrderedDict()})
        persons = fam["persons"]
        if r.person_id not in persons:
            persons[r.person_id] = {"identifier": r.person_id}
        person = persons[r.person_id]
        if r.sex:
            if "sex" in person and person["sex"] != r.sex:
                raise HardValidationError(f"Sex conflict for {r.family_id}/{r.person_id} at line {r._line}")
            person["sex"] = r.sex
        if r.mother_id:
            person["motherIdentifier"] = r.mother_id
        if r.father_id:
            person["fatherIdentifier"] = r.father_id
        if r.note:
            person["comment"] = r.note
    return [
        {"identifier": fam["identifier"], "persons": list(fam["persons"].values())}
        for fam in families.values()
    ]


def build_files(rows: List[TsvRow]) -> List[Dict[str, Any]]:
    files: Dict[Tuple[str, str], Dict[str, Any]] = OrderedDict()
    for r in rows:
        key = (r.filename, r.checksum)
        if key not in files:
            files[key] = {
                "checksum": r.checksum,
                "filename": r.filename,
                "assembly": r.assembly,
                "fileType": r.file_type,
                "priority": r.priority,
                "run": r.run,
                "samples": [],
            }
        sample = {"name": r.sample, "person": r.person_id}
        if r.bam_path:
            sample["bamPath"] = r.bam_path
        files[key]["samples"].append(sample)
    return list(files.values())


def build_interpretations(rows: List[TsvRow]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[TsvRow]] = OrderedDict()
    for r in rows:
        groups.setdefault(r.interpretation_title, []).append(r)

    interps: Dict[str, Dict[str, Any]] = OrderedDict()
    for title, grp in groups.items():
        ensure_single_index(grp, title)
        idxs = [r for r in grp if r.is_index]
        info = {
            "title": title,
            "project": grp[0].project,
            "assignee": grp[0].assignee,
            "priority": grp[0].priority or "normal",
            "indexCase": idxs[0].person_id if idxs else None,
            "datas": OrderedDict(),
        }
        for r in grp:
            dtype = r.file_type or "SNV"
            dtitle = r.data_title or dtype
            dkey = (dtype, dtitle)
            if dkey not in info["datas"]:
                info["datas"][dkey] = {
                    "type": dtype,
                    "title": dtitle,
                    "samples": [],
                    "isCohort": bool(r.is_cohort),
                    "pretags": None,
                }
            data = info["datas"][dkey]
            sample = {"name": r.sample, "checksum": r.checksum}
            if r.is_dataset_index:
                sample["isDatasetIndex"] = True
            data["samples"].append(sample)
            if data["pretags"] is None and r.pretags is not None:
                data["pretags"] = [p.model_dump() for p in r.pretags]
            if r.is_cohort:
                data["isCohort"] = True
        info["datas"] = list(info["datas"].values())
        interps[title] = info
    return list(interps.values())


def build_payload(rows: List[TsvRow]) -> Dict[str, Any]:
    # validate no sample+checksum maps to multiple persons across rows
    mapping: Dict[Tuple[str, str], str] = {}
    for r in rows:
        key = (r.sample, r.checksum)
        if key in mapping and mapping[key] != r.person_id:
            raise HardValidationError(
                f"Sample+checksum {key} maps to multiple persons: "
                f"{mapping[key]} vs {r.person_id} at line {r._line}"
            )
        mapping[key] = r.person_id

    return {
        "families": build_families(rows),
        "files": build_files(rows),
        "interpretations": build_interpretations(rows),
    }
