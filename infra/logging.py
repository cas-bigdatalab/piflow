from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from infra.config_loader import get_settings, resolve_workspace_root


_LOGGING_INITIALIZED = False


def _resolve_level(level_name: str, debug: bool) -> int:
    if level_name:
        level = getattr(logging, level_name.upper(), None)
        if isinstance(level, int):
            return level
    return logging.DEBUG if debug else logging.INFO


def init_logging(force: bool = False) -> None:
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED and not force:
        return

    settings = get_settings()
    app_cfg = settings.app
    workspace_cfg = settings.workspace

    logs_dir = resolve_workspace_root(workspace_cfg.root) / workspace_cfg.dirs.logs
    logs_dir.mkdir(parents=True, exist_ok=True)

    level = _resolve_level(app_cfg.log_level, app_cfg.debug)
    log_file = logs_dir / app_cfg.log_file

    logger = logging.getLogger("flow")
    logger.setLevel(level)
    logger.propagate = False

    # 清理旧 handler
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 每天一个日志文件
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",        # 每天切割
        interval=1,
        backupCount=app_cfg.log_backup_count,
        encoding="utf-8",
    )

    # 日期后缀
    file_handler.suffix = "%Y-%m-%d"

    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # 控制台日志
    if app_cfg.log_to_console:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    _LOGGING_INITIALIZED = True

    logging.getLogger("flow.bootstrap").info(
        "logging initialized file=%s level=%s",
        log_file,
        logging.getLevelName(level),
    )
