from __future__ import annotations

import json
from pathlib import Path

from piflow_engine.cn.piflow.remote.result_resolver import ResultResolver


def test_result_resolver_falls_back_to_stop_log_output(tmp_path: Path) -> None:
    output_file = tmp_path / "remote.txt"
    output_file.write_text("remote artifact", encoding="utf-8")
    log_path = tmp_path / "job.log"
    log_path.write_text(
        json.dumps(
            {
                "event": "STOP_COMPLETED",
                "payload": {
                    "outputs": {
                        "output": {
                            "type": "file",
                            "path": str(output_file),
                        }
                    }
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    resolver = ResultResolver()
    resolved = resolver._resolve_path_from_stop_log(
        log_path=str(log_path),
        result_output_name="",
    )

    assert resolved == output_file.resolve()


def test_result_resolver_prefers_named_output_from_stop_log(tmp_path: Path) -> None:
    left_output = tmp_path / "left.txt"
    right_output = tmp_path / "right.txt"
    left_output.write_text("left", encoding="utf-8")
    right_output.write_text("right", encoding="utf-8")
    log_path = tmp_path / "job.log"
    log_path.write_text(
        json.dumps(
            {
                "event": "STOP_COMPLETED",
                "payload": {
                    "outputs": {
                        "left": {"type": "file", "path": str(left_output)},
                        "right": {"type": "file", "path": str(right_output)},
                    }
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    resolver = ResultResolver()
    resolved = resolver._resolve_path_from_stop_log(
        log_path=str(log_path),
        result_output_name="right",
    )

    assert resolved == right_output.resolve()
