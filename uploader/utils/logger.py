import logging
import re
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_CONSOLE_FORMAT = "%(asctime)s [%(levelname)-8s] %(message)s"
_FILE_FORMAT    = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FORMAT    = "%Y-%m-%d %H:%M:%S"


def _make_namer(base_path: Path):
    """Return a namer that moves the date suffix before the extension.

    Default: uploader.log.2026-04-14
    With namer: uploader.2026-04-14.log
    """
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    def namer(default_name: str) -> str:
        # default_name ends with the date suffix added by the handler
        date_part = re.search(r"\d{4}-\d{2}-\d{2}.*$", default_name)
        date = date_part.group() if date_part else Path(default_name).suffix.lstrip(".")
        return str(parent / f"{stem}.{date}{suffix}")

    return namer


def setup_logger(config: dict) -> None:
    """Configure the uploader logger from the config dict.

    Console handler level is controlled by logging.log_level (default INFO).
    File handler always logs at DEBUG when logging.log_directory is set.
    Rotation is controlled by log_rotation_when / log_rotation_interval / log_backup_count.
    Files older than backupCount × interval are deleted automatically.
    All child loggers (uploader.*) inherit these handlers automatically.
    """
    log_cfg = config.get("logging", {})
    console_level = getattr(logging, log_cfg.get("log_level", "INFO").upper(), logging.INFO)
    log_dir = log_cfg.get("log_directory")

    root = logging.getLogger("uploader")
    root.setLevel(logging.DEBUG)

    if root.handlers:
        return  # already configured; avoid duplicate handlers on repeated calls

    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(logging.Formatter(_CONSOLE_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(console)

    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / "uploader.log"

        fh = TimedRotatingFileHandler(
            log_file,
            when=log_cfg.get("log_rotation_when", "W0"),
            interval=log_cfg.get("log_rotation_interval", 1),
            backupCount=log_cfg.get("log_backup_count", 52),
            encoding="utf-8",
        )
        fh.namer = _make_namer(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))
        root.addHandler(fh)
