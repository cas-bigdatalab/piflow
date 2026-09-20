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


@pytest.mark.parametrize("node_id", ["direct-result-save", "another-file-producer"])
@pytest.mark.parametrize("output_name", ["", "output"])
def test_direct_file_metadata_and_download_without_workspace(tmp_path, monkeypatch, node_id, output_name):
    path = tmp_path / "export" / "result.csv"
    path.parent.mkdir()
    content = b"timestamp,value\n2026-09-01,12\n"
    path.write_bytes(content)
    resolver = ResultResolver()

    def find_row(*, run_id, result_node_id):
        assert run_id == "run-1"
        assert result_node_id == node_id
        return dict(flow_status="SUCCESS", stop_status="SUCCESS", stop_uuid=node_id,
                    final_output_path=str(path), stop_workspace_path="")

    monkeypatch.setattr(resolver, "_find_result_row", find_row)
    request = dict(run_id="run-1", result_node_id=node_id, result_output_name=output_name)
    meta = resolver.get_result_meta(**request)
    assert meta.file_name == path.name
    assert meta.file_size == len(content)
    with resolver.open_result_file(**request) as stream:
        assert stream.read() == content


@pytest.mark.parametrize("output_name,code", [
    ("unknown", "RESULT_NOT_FOUND"),
    ("result.csv", "RESULT_NOT_FOUND"),
    ("output/child.csv", "RESULT_NOT_FOUND"),
    ("../secret", "INVALID_ARGUMENT"),
    ("nested/../../secret", "INVALID_ARGUMENT"),
    ("/tmp/secret", "INVALID_ARGUMENT"),
])
def test_direct_file_does_not_ignore_output_selector(tmp_path, output_name, code):
    path = tmp_path / "result.csv"
    path.write_text("result", encoding="utf-8")
    with pytest.raises(RemoteExecutionError) as caught:
        ResultResolver()._resolve_node_result_path(
            row={"stop_uuid": "save", "final_output_path": str(path)},
            result_output_name=output_name,
        )
    assert caught.value.code == code


def test_direct_file_still_requires_file_to_exist(tmp_path, monkeypatch):
    resolver = ResultResolver()
    monkeypatch.setattr(resolver, "_find_result_row", lambda **_: dict(
        flow_status="SUCCESS", stop_uuid="save", final_output_path=str(tmp_path / "missing.csv")))
    with pytest.raises(RemoteExecutionError) as caught:
        resolver.get_result_meta(run_id="run-1", result_node_id="save", result_output_name="output")
    assert caught.value.code == "RESULT_FILE_NOT_FOUND"


def test_node_without_either_recorded_path_is_rejected():
    with pytest.raises(RemoteExecutionError) as caught:
        ResultResolver()._resolve_node_result_path(row={"stop_uuid": "save"}, result_output_name="output")
    assert caught.value.code == "RESULT_NOT_FOUND"


@pytest.mark.parametrize("output_name", ["", "output", "nested/result.csv"])
def test_existing_workspace_output_retains_priority(tmp_path, output_name):
    workspace = tmp_path / "stop"
    final = tmp_path / "export.csv"
    final.write_text("different result", encoding="utf-8")
    resolved = ResultResolver()._resolve_node_result_path(
        row={"stop_uuid": "command", "stop_workspace_path": str(workspace), "final_output_path": str(final)},
        result_output_name=output_name,
    )
    assert resolved == (workspace / "output" / output_name).resolve()


def test_unspecified_node_still_uses_final_output_path(tmp_path, monkeypatch):
    path = tmp_path / "result.csv"
    path.write_bytes(b"result")
    resolver = ResultResolver()
    monkeypatch.setattr(resolver, "_find_result_row", lambda **_: dict(
        flow_status="SUCCESS", final_output_path=str(path)))
    with resolver.open_result_file(run_id="run-1", result_node_id="", result_output_name="") as stream:
        assert stream.read() == b"result"


def test_unfinished_run_cannot_download_recorded_final_file(tmp_path, monkeypatch):
    path = tmp_path / "result.csv"
    path.write_bytes(b"result")
    resolver = ResultResolver()
    monkeypatch.setattr(resolver, "_find_result_row", lambda **_: dict(
        flow_status="RUNNING", stop_uuid="save", final_output_path=str(path)))
    with pytest.raises(RemoteExecutionError) as caught:
        resolver.get_result_meta(run_id="run-1", result_node_id="save", result_output_name="output")
    assert caught.value.code == "RUN_NOT_FINISHED"


def test_direct_directory_result_is_archived_without_workspace(tmp_path, monkeypatch):
    import io
    import zipfile

    directory = tmp_path / "export"
    directory.mkdir()
    (directory / "result.csv").write_bytes(b"result")
    resolver = ResultResolver()
    monkeypatch.setattr(resolver, "_find_result_row", lambda **_: dict(
        flow_status="SUCCESS", stop_uuid="save", final_output_path=str(directory)))
    request = dict(run_id="run-1", result_node_id="save", result_output_name="output")
    meta = resolver.get_result_meta(**request)
    assert meta.file_name.endswith(".zip")
    with resolver.open_result_file(**request) as stream:
        data = stream.read()
    assert len(data) == meta.file_size
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.namelist() == ["result.csv"]
        assert archive.read("result.csv") == b"result"
