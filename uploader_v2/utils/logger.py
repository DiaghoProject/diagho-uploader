import logging
from pathlib import Path

_CONSOLE_FORMAT = "%(asctime)s [%(levelname)-8s] %(message)s"
_FILE_FORMAT    = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FORMAT    = "%Y-%m-%d %H:%M:%S"


def setup_logger(config: dict) -> None:
    """Configure the uploader_v2 logger from the config dict.

    Console handler level is controlled by logging.log_level (default INFO).
    File handler always logs at DEBUG when logging.log_directory is set.
    All child loggers (uploader_v2.*) inherit these handlers automatically.
    """
    log_cfg = config.get("logging", {})
    console_level = getattr(logging, log_cfg.get("log_level", "INFO").upper(), logging.INFO)
    log_dir = log_cfg.get("log_directory")

    root = logging.getLogger("uploader_v2")
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
        fh = logging.FileHandler(log_path / "uploader.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))
        root.addHandler(fh)
