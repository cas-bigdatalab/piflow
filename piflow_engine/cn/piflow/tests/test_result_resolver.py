from __future__ import annotations

from pathlib import Path

import pytest

from piflow_engine.cn.piflow.remote.result_resolver import (
    RemoteExecutionError,
    ResultResolver,
)


def test_result_resolver_archives_directory_to_workspace_temp(tmp_path: Path) -> None:
    stop_workspace = tmp_path / "stop"
    output_dir = stop_workspace / "output" / "openbabel"
    nested_dir = output_dir / "nested"
    nested_dir.mkdir(parents=True)
    (output_dir / "primary.gjf").write_text("gjf", encoding="utf-8")
    (nested_dir / "summary.md").write_text("summary", encoding="utf-8")

    resolver = ResultResolver()
    archive_path = resolver._archive_result_directory(
        output_dir,
        temp_root=stop_workspace / "temp",
    )

    assert archive_path.parent == stop_workspace / "temp"
    assert archive_path.is_file()
    assert not archive_path.is_relative_to(output_dir)

    import zipfile

    with zipfile.ZipFile(archive_path) as archive:
        assert sorted(archive.namelist()) == [
            "nested/summary.md",
            "primary.gjf",
        ]


def test_result_resolver_reuses_stable_directory_archive(tmp_path: Path) -> None:
    directory = tmp_path / "stop" / "output"
    directory.mkdir(parents=True)
    (directory / "result.txt").write_text("result", encoding="utf-8")
    temp_root = tmp_path / "stop" / "temp"

    resolver = ResultResolver()
    first = resolver._archive_result_directory(directory, temp_root=temp_root)
    second = resolver._archive_result_directory(directory, temp_root=temp_root)

    assert first == second


def test_result_resolver_resolves_relative_output_path(tmp_path: Path) -> None:
    stop_workspace = tmp_path / "stop"
    result = stop_workspace / "output" / "outputs" / "openbabel" / "acetic.gjf"
    result.parent.mkdir(parents=True)
    result.write_text("gjf", encoding="utf-8")

    resolver = ResultResolver()
    resolved = resolver._resolve_node_result_path(
        row={"stop_workspace_path": str(stop_workspace), "stop_uuid": "node-1"},
        result_output_name="outputs/openbabel/acetic.gjf",
    )

    assert resolved == result.resolve()


@pytest.mark.parametrize(
    "result_output_name",
    ["/tmp/secret.txt", "../secret.txt", "nested/../../secret.txt"],
)
def test_result_resolver_rejects_result_path_escape(
    tmp_path: Path,
    result_output_name: str,
) -> None:
    resolver = ResultResolver()

    with pytest.raises(RemoteExecutionError, match="relative path|stay inside"):
        resolver._resolve_node_result_path(
            row={"stop_workspace_path": str(tmp_path / "stop"), "stop_uuid": "node-1"},
            result_output_name=result_output_name,
        )
