# diagho-uploader

Automated pipeline bridge for [Diagho](https://diagho.fr): watches input directories, uploads genomic biofiles (VCF, BED-like CNV tabfiles), and posts the associated metadata configuration to the Diagho API. Designed to run as a long-lived background daemon at the end of bioinformatics pipelines.

---

## How it works

The uploader runs a state machine that processes one ingestion job at a time:

```
WAITING_METADATA → WAITING_BIOFILES → UPLOADING_BIOFILES → WAITING_PARSING → POSTING_METADATA → DONE
                                                                                                   ↓
                                                                                             (reset, next job)
```

| State | What happens |
|---|---|
| `WAITING_METADATA` | Polls `metadata_dir` for a `.tsv` or `.json` file. When found, parses and validates it, then archives it. |
| `WAITING_BIOFILES` | Polls `files_dir` until all biofiles declared in the metadata are present. Fails after `biofile_timeout_minutes`. |
| `UPLOADING_BIOFILES` | Uploads each biofile to the API. Retries up to 5 times per file on transient errors; already-uploaded files are skipped by checksum. Archived on success. |
| `WAITING_PARSING` | Polls the API until all uploaded biofiles have finished server-side parsing. |
| `POSTING_METADATA` | Posts the full metadata configuration (families, interpretations, etc.) to the API. |
| `DONE` / `FAILED` | Sends an email notification, resets, and waits for the next metadata file. |

---

## Requirements

- Python 3.10+
- Access to a running Diagho API instance

---

## Installation

```bash
git clone https://github.com/DiaghoProject/diagho-uploader.git
cd diagho-uploader
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration

Copy the example config and fill in your values:

```bash
cp config/config.example.yaml config/config.yaml
```

`config/config.yaml` is gitignored and will never be committed.

### Reference

#### Directories

| Key | Description |
|---|---|
| `metadata_dir` | Drop TSV or JSON metadata files here. Processed files are archived automatically. |
| `files_dir` | Drop biofiles (VCF, CNV tabfiles, etc.) here. |
| `archives_dir` | Destination for processed metadata files and uploaded biofiles. |

#### API

```yaml
diagho_api:
  url: "http://hostname:8080/api/v1/"
  username: ""
  password: ""
  allow_insecure: true   # disable SSL verification — use for self-signed certs or plain HTTP
```

#### Genome accessions

Maps assembly names used in metadata TSV rows to their numeric IDs in your Diagho instance:

```yaml
accessions:
  GRCh37: 1
  GRCh38: 2
```

The names must match what is used in the `assembly` column of your TSV files.

#### CNV tabfile settings

```yaml
tabfiles_columns_index: {"1": "CHROM", "2": "START", "3": "END"}
tabfiles_zero_based: true   # true for BED (0-based), false for 1-based formats
```

`tabfiles_columns_index` maps 1-based column positions to the expected column names as configured in Diagho.

#### Biofile timeout

```yaml
biofile_timeout_minutes: 60   # optional — default 60
```

How long to wait for expected biofiles to appear in `files_dir` before failing the job.

#### Deduplication

```yaml
dedup_biofiles: false   # remove duplicate variants in uploaded biofiles
```

#### Email notifications

```yaml
emails:
  send_mail_flag: 1
  recipients: "user@example.com"   # comma-separated for multiple recipients

smtp:
  server: "mailserver"
  port: 25
  use_tls: false
  from_email_format: "diagho-uploader-{hostname}@example.com"
  username:   # leave blank for open relay
  password:   # leave blank for open relay
```

An alert email is sent on job failure; an info email is sent on success. Set `send_mail_flag: 0` to disable.

#### Logging

```yaml
logging:
  log_level: "INFO"           # DEBUG, INFO, WARNING, ERROR
  log_directory: "path/to/logs"
  log_rotation_when: "W0"     # W0 = every Monday; see TimedRotatingFileHandler docs
  log_rotation_interval: 1
  log_backup_count: 52        # keep 52 weekly rotations (≈ 1 year)
```

Logs are always printed to the console. File logging is enabled when `log_directory` is set. Log files are named `uploader.YYYY-MM-DD.log`.

---

## Running

All operations go through `diagho_uploader.sh`:

```
Usage: diagho_uploader.sh <command> [options]

Commands:
  --start           Start the uploader in the background (daemon mode)
  --start --debug   Start in the foreground with live output
  --stop            Send a graceful shutdown signal (finishes current step)
  --stop --force    Kill the process immediately
  --status          Show whether the uploader is running
  --update          Stop, pull latest changes, reinstall deps, restart
  --parse           Wait for a TSV/JSON in metadata_dir, print the validated
                    JSON payload to stdout, then exit (no API calls, no logs)

Options:
  --config <path>   Path to config YAML (default: config/config.yaml)
  --help            Show this help message
```

### Validate a metadata file without running the pipeline

`--parse` is useful for checking that a TSV file produces the expected API payload before running a real ingestion:

```bash
# drop a file into metadata_dir, then:
./diagho_uploader.sh --parse
```

Polls `metadata_dir`, prints the validated JSON to stdout when a file appears, and exits. No API calls are made. SIGTERM / Ctrl-C cancels the wait.

---

## Metadata TSV format

The metadata file describes one or more biofiles and their associated clinical/family context. Each row represents one sample on one biofile within one interpretation.

Multiple rows sharing the same `filename` / `checksum` define multiple samples on the same file. Multiple rows sharing the same `interpretation_title` define the samples and data blocks within one interpretation.

### Columns

| Column | Required | Values / format | Description |
|---|---|---|---|
| `filename` | yes | string | Biofile filename (must be present in `files_dir`) |
| `checksum` | yes | MD5 hex string | MD5 checksum of the biofile |
| `file_type` | yes | `SNV`, `CNV` | Biofile type |
| `assembly` | yes | e.g. `GRCh37`, `GRCh38` | Genome assembly — must match a key in `accessions` config |
| `sample` | yes | string | Sample name |
| `bam_path` | no | path string | Path to associated BAM file |
| `run` | no | string | Run identifier |
| `family_id` | yes | string | Family identifier |
| `person_id` | yes | string | Person identifier |
| `father_id` | no | string | `person_id` of the father |
| `mother_id` | no | string | `person_id` of the mother |
| `sex` | no | `male`, `female`, `unknown` | Biological sex |
| `first_name` | no | string | |
| `last_name` | no | string | |
| `date_of_birth` | no | `YYYY-MM-DD` | |
| `note` | no | string | Free-text note attached to the person |
| `interpretation_title` | yes | string | Groups rows into one interpretation |
| `is_index` | yes* | `0` / `1` | Marks index cases of the interpretation — **at least one `1` per interpretation; multiple allowed** |
| `is_dataset_index` | no | `0` / `1` | Marks the index of non cohort dataset — at most one `1` per data block |
| `data_title` | no | string | Label for the data block within the interpretation |
| `project` | yes | string | Project identifier in Diagho |
| `assignee` | no | string | Username to assign the interpretation to |
| `priority` | no | `low`, `normal`, `high`, `highest` | Defaults to `normal` |
| `is_cohort` | no | `0` / `1` | Whether this is a cohort analysis |
| `pretags` | no | JSON array | Pre-applied tags: `[{"tag_id": N, "filter_id": N}, ...]` |

### Notes

- A TSV with no header row, or missing required columns, will fail at `WAITING_METADATA` and transition the job to `FAILED`.
- Interpretation block (column interpretation_title and following) is optional if only upload of biofiles and their assignation to persons is needed. 
- `priority` also accepts legacy integer values: `0` = low, `1` = normal, `2` = high, `3` = highest.
- `is_index` marks the persons for whom the interpretation is created. Multiple rows in the same interpretation can have `is_index = 1`; the API receives the full list. `is_dataset_index` is the central sample of a dataset and columns of related persons will be renamed accordingly (eg INDEX, MOTHER, FATHER…).
- Invalid `pretags` (malformed JSON) are dropped with a warning rather than failing the whole job.

---

## Development

### Install dev dependencies

```bash
pip install -r requirements-dev.txt
```

### Run unit tests

```bash
pytest tests/unit/
```

### Run integration tests

Integration tests require a live Diagho API. Populate `config/config.yaml` with valid credentials, then:

```bash
pytest -m integration
```

Integration tests are skipped automatically when `config/config.yaml` is absent.

---

## Project structure

```
diagho-uploader/
├── main.py                        # Entry point
├── diagho_uploader.sh             # CLI wrapper (start/stop/parse/…)
├── config/
│   └── config.example.yaml        # Configuration template
├── uploader/
│   ├── runner.py                  # Main loop and state machine driver
│   ├── context.py                 # Immutable runtime context (dirs, API client, settings)
│   ├── job/
│   │   ├── model.py               # IngestionJob — mutable per-job state
│   │   ├── states.py              # JobState enum
│   │   ├── dispatch.py            # Step dispatch table and sleep policy
│   │   └── steps/                 # One module per state
│   ├── metadata/
│   │   ├── parser.py              # TSV → List[TsvRow]
│   │   ├── builder.py             # List[TsvRow] → raw payload dict
│   │   ├── validator.py           # Raw dict → validated dict (Pydantic)
│   │   ├── tsv_schema.py          # TsvRow model and field validators
│   │   └── payload_schema.py      # API payload models
│   ├── services/
│   │   └── biofiles_uploader.py   # SNV / CNV upload logic
│   ├── infrastructure/api/
│   │   ├── client.py              # ApiClient — all HTTP calls
│   │   ├── auth.py                # JWT auth handler (in-memory tokens)
│   │   ├── endpoints.py           # URL builder
│   │   └── exceptions.py          # API exception hierarchy
│   └── utils/
│       ├── logger.py              # Logging setup with file rotation
│       └── mailer.py              # SMTP email notifications
├── tests/
│   ├── conftest.py                # Shared fixtures and synthetic test data
│   ├── unit/
│   │   ├── test_metadata_pipeline.py
│   │   ├── test_auth.py
│   │   └── test_steps.py
│   └── integration/
│       └── test_api.py
├── requirements.txt
└── requirements-dev.txt
```
