from typing import Optional, List

from pydantic import BaseModel, Field

from .tsv_schema import Sex, DataType, Priority, PretagItem


class Person(BaseModel):
    identifier: str
    sex: Optional[Sex] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    birthday: Optional[str] = None
    motherIdentifier: Optional[str] = None
    fatherIdentifier: Optional[str] = None
    comment: Optional[str] = None

class Family(BaseModel):
    identifier: str
    comment: Optional[str] = None
    persons: List[Person]


class FileSample(BaseModel):
    name: str
    person: str
    bamPath: Optional[str] = None

class File(BaseModel):
    checksum: str
    filename: str
    samples: List[FileSample]
    assembly: str
    fileType: DataType
    priority: str = Field(default=Priority.normal)
    run: Optional[str] = None


class InterpretationSample(BaseModel):
    name: str
    checksum: str
    isDatasetIndex: Optional[bool] = None

class DataBlock(BaseModel):
    type: DataType
    title: str
    samples: List[InterpretationSample]
    isCohort: bool = False
    pretags: Optional[list[PretagItem]] = None

class Interpretation(BaseModel):
    title: str
    project: str
    assignee: Optional[str] = None
    indexCase: str
    priority: str = Priority.normal
    datas: List[DataBlock]


class MetadataPayload(BaseModel):
    families: List[Family]
    files: List[File]
    interpretations: List[Interpretation]
