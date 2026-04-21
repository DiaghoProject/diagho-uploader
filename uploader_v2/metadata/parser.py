import csv
from typing import List
from uploader_v2.metadata.tsv_schema import TsvRow


def parse_tsv_rows(tsv_text: str) -> List[TsvRow]:
    reader = csv.DictReader(tsv_text.splitlines(), delimiter="\t")
    rows = []
    for i, raw in enumerate(reader, start=2):  # line numbers (account for header)
        norm = {k: (v.strip() if isinstance(v, str) else v) for k, v in raw.items()}
        norm["_line"] = i
        try:
            r = TsvRow(**norm)
            r._line = i
            rows.append(r)
        except Exception as e:
            raise ValueError(f"TSV parse error at line {i}: {e}") from e
    return rows
