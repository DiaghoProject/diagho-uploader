import csv
from typing import List

from .tsv_schema import TsvRow


def parse_tsv_rows(text: str, delimiter: str = "\t") -> List[TsvRow]:
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    rows = []
    for i, raw in enumerate(reader, start=2):  # start=2: header is line 1
        norm = {k: (v.strip() if isinstance(v, str) else v) for k, v in raw.items()}
        try:
            r = TsvRow(**norm)
            r._line = i
            rows.append(r)
        except Exception as e:
            raise ValueError(f"Parse error at line {i}: {e}") from e
    return rows
