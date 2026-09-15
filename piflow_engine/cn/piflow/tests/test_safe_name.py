from __future__ import annotations

from piflow_engine.cn.piflow.runtime.logging.path_utils import safe_name
from piflow_engine.cn.piflow.runtime.logging.run_logger import RunLogger


def test_safe_name_normalizes_and_preserves_chinese() -> None:
    assert safe_name("  中文 / 名称:\\*?<>|  ") == "中文_名称"


def test_run_logger_uses_safe_name_for_stop_logs(tmp_path) -> None:
    logger = RunLogger(tmp_path)
    path = logger.stop_log_path("process_1", "中文 / 名称:\\*?<>|")

    assert path == tmp_path / "process_1" / "stops" / "中文_名称" / "job.log"
