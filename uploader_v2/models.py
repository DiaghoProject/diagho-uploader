from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import json

class HardValidationError(Exception):
    pass

class SoftValidationWarning(Warning):
    pass

class PretagItem(BaseModel):
    tag_id: int
    filter_id: int

class TsvRow(BaseModel):
    filename: str
    checksum: Optional[str] = None
    file_type: str = Field(default="SNV")
    assembly: str

    sample: str
    bam_path: Optional[str] = None
    run: Optional[str] = None

    family_id: str
    person_id: str
    father_id: Optional[str] = None
    mother_id: Optional[str] = None

    sex: Optional[str] = None
    is_affected: Optional[bool] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    note: Optional[str] = None

    interpretation_title: str
    is_index: Optional[bool] = Field(default=False)
    data_title: Optional[str] = None
    project: str
    assignee: Optional[str] = None
    priority: str = Field(default="normal")

    is_cohort: Optional[bool] = Field(default=False)
    pretags: Optional[List[PretagItem]] = None

    # internal for error reporting (set by parser)
    _line: Optional[int] = None

    @field_validator("checksum", mode="before")
    def normalize_checksum(cls, v):
        if v is None or v == "":
            return None
        # take first token before comma to handle CSV quirks
        return str(v).split(",")[0]

    @field_validator("is_affected", "is_index", "is_cohort", mode="before")
    def parse_bool(cls, v):
        if v is None or v == "":
            return False
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in ("1", "true", "yes", "y", "t"):
            return True
        if s in ("0", "false", "no", "n", "f"):
            return False
        return False

    @field_validator("pretags", mode="before")
    def parse_pretags(cls, v):
        if v in (None, "", "null"):
            return None
        if isinstance(v, list):
            return v
        # try parse json; fallback to single-quote repair; if both fail, return None
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("pretags must be a list")
            return parsed
        except Exception:
            try:
                parsed = json.loads(v.replace("'", '"'))
                if not isinstance(parsed, list):
                    raise ValueError("pretags must be a list")
                return parsed
            except Exception:
                return None
            