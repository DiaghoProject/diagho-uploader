from collections import OrderedDict
from typing import List, Dict, Any, Tuple
from models import TsvRow, HardValidationError, PretagItem
import logging

logger = logging.getLogger("uploader_v2")

def ensure_single_index(interp_rows: List[TsvRow], title: str):
    indexes = list(set((r.person_id, r.is_index) for r in interp_rows if r.is_index))
    print(indexes)
    if len(indexes) > 1:
        raise HardValidationError(f"Interpretation '{title}' has multiple index cases: {indexes}")
    if len(indexes) == 0:
        raise HardValidationError(f"Interpretation '{title}' has no index case (required)")

def validate_pretags_list(raw):
    if raw is None:
        return None
    validated = []
    for item in raw:
        if not isinstance(item, dict):
            logger.warning("Pretag item not a dict, dropping it")
            continue
        if "tag_id" not in item or "filter_id" not in item:
            logger.warning("Pretag missing tag_id or filter_id, dropping it")
            continue
        try:
            tag_id = int(item["tag_id"])
            filter_id = int(item["filter_id"])
        except Exception:
            logger.warning("Pretag tag_id/filter_id not int, dropping it")
            continue
        validated.append({"tag_id": tag_id, "filter_id": filter_id})
    return validated or None

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
    out = []
    for fam in families.values():
        out.append({"identifier": fam["identifier"], "persons": list(fam["persons"].values())})
    return out

def build_files(rows: List[TsvRow]) -> List[Dict[str, Any]]:
    files: Dict[Tuple[str, str], Dict[str, Any]] = OrderedDict()
    for r in rows:
        key = (r.filename, r.checksum)
        if key not in files:
            files[key] = {"checksum": r.checksum, "filename": r.filename, "samples": [], "run": r.run}
        sample_obj = {"name": r.sample, "person": r.person_id}
        if r.bam_path:
            sample_obj["bamPath"] = r.bam_path
        files[key]["samples"].append(sample_obj)
    return list(files.values())

def build_interpretations(rows: List[TsvRow]) -> List[Dict[str, Any]]:
    interps: Dict[str, Dict[str, Any]] = OrderedDict()
    groups: Dict[str, List[TsvRow]] = OrderedDict()
    for r in rows:
        groups.setdefault(r.interpretation_title, []).append(r)
    for title, grp in groups.items():
        ensure_single_index(grp, title)
        info = {
            "title": title,
            "assignee": grp[0].assignee,
            "project": grp[0].project,
            "priority": grp[0].priority or "normal",
            "indexCase": None,
            "datas": OrderedDict()
        }
        idxs = [r for r in grp if r.is_index]
        info["indexCase"] = idxs[0].person_id if idxs else None
        for r in grp:
            dtype = r.file_type or "SNV"
            dtitle = r.data_title or dtype
            dkey = (dtype, dtitle)
            if dkey not in info["datas"]:
                info["datas"][dkey] = {
                    "type": dtype,
                    "title": dtitle,
                    "pretags": None,
                    "samples": [],
                    "isCohort": bool(r.is_cohort)
                }
            data = info["datas"][dkey]
            samp = {"name": r.sample, "isAffected": bool(r.is_affected), "checksum": r.checksum}
            data["samples"].append(samp)
            if data["pretags"] is None and r.pretags is not None:
                data["pretags"] = validate_pretags_list(r.pretags)
            if r.is_cohort:
                data["isCohort"] = True
        info["datas"] = list(info["datas"].values())
        interps[title] = info
    return list(interps.values())

def build_payload(rows: List[TsvRow]) -> Dict[str, Any]:
    mapping = {}
    for r in rows:
        key = (r.sample, r.checksum)
        if key in mapping and mapping[key] != r.person_id:
            raise HardValidationError(f"Sample+checksum {key} mapped to multiple persons: {mapping[key]} vs {r.person_id} at line {r._line}")
        mapping[key] = r.person_id
    return {
        "families": build_families(rows),
        "files": build_files(rows),
        "interpretations": build_interpretations(rows)
    }
