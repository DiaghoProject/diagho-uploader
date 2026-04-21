import json
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class HardValidationError(Exception):
    pass


class Priority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    highest = "highest"

LEGACY_PRIORITY_MAP = {
    0: Priority.low,
    1: Priority.normal,
    2: Priority.high,
    3: Priority.highest,
}

class Sex(str, Enum):
    male = "male"
    female = "female"
    unknown = "unknown"

class DataType(str, Enum):
    SNV = "SNV"
    CNV = "CNV"


class PretagItem(BaseModel):
    tag_id: int
    filter_id: int


class TsvRow(BaseModel):
    filename: str
    checksum: Optional[str] = None
    file_type: DataType = Field(DataType.SNV)
    assembly: str

    sample: str
    bam_path: Optional[str] = None
    run: Optional[str] = None

    family_id: str
    person_id: str
    father_id: Optional[str] = None
    mother_id: Optional[str] = None

    sex: Sex = Field(default=Sex.unknown)
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
    priority: str = Field(default=Priority.normal)

    is_cohort: Optional[bool] = Field(default=False)
    pretags: Optional[List[PretagItem]] = None

    # set by parser for error reporting; not a Pydantic field
    _line: int = 0

    @field_validator("assignee", mode="before")
    def empty_assignee_to_none(cls, v):
        if v is None or v == "":
            return None
        return v

    @field_validator("checksum", mode="before")
    def normalize_checksum(cls, v):
        if v is None or v == "":
            return None
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

    @field_validator("priority", mode="before")
    def parse_priority(cls, v):
        if v in (None, "", "null"):
            return Priority.normal
        try:
            i = int(v)
        except Exception:
            i = None
        if i is not None:
            return LEGACY_PRIORITY_MAP.get(i, Priority.normal)
        try:
            return Priority(str(v).lower())
        except Exception:
            return Priority.normal

    @field_validator("pretags", mode="before")
    def parse_pretags(cls, v):
        if v in (None, "", "null"):
            return None
        if isinstance(v, list):
            return v
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
