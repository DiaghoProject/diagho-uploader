from enum import Enum, auto

class JobState(Enum):
    WAITING_METADATA = auto()
    WAITING_BIOFILES = auto()
    UPLOADING_BIOFILES = auto()
    WAITING_PARSING = auto()
    POSTING_METADATA = auto()
    DONE = auto()
    FAILED = auto()
