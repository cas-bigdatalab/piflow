from __future__ import annotations

import logging
import sys
from pathlib import Path


DEFAULT_LOG_FORMAT = (
    "%(asctime)s %(levelname)s [%(name)s] "
    "%(filename)s:%(lineno)d - %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_PATH = Path("logs") / "piflow.log"


def configure_piflow_logging(
    *,
    level: int | str = logging.INFO,
    log_path: str | Path = DEFAULT_LOG_PATH,
    console: bool = True,
    file: bool = True,
    force: bool = False,
) -> None:
    logger = logging.getLogger("piflow")
    if logger.handlers and not force:
        return

    logger.setLevel(_normalize_level(level))
    logger.propagate = False

    if force:
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(_normalize_level(level))
        logger.addHandler(console_handler)

    if file:
        path = Path(log_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(_normalize_level(level))
        logger.addHandler(file_handler)


def get_logger(name: str | None = None) -> logging.Logger:
    if not logging.getLogger("piflow").handlers:
        configure_piflow_logging()

    if not name:
        return logging.getLogger("piflow")

    if name == "piflow" or name.startswith("piflow."):
        return logging.getLogger(name)

    return logging.getLogger(f"piflow.{name}")


def _normalize_level(level: int | str) -> int:
    if isinstance(level, int):
        return level

    normalized = level.upper()
    value = logging.getLevelName(normalized)
    if isinstance(value, int):
        return value

    raise ValueError(f"invalid log level: {level}")
