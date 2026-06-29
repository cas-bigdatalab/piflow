from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from cn.piflow.core.flow_bean import FlowBean
from cn.piflow.core.runner import Runner
from cn.piflow.engine.local.constants import (
    RUNNER_CONTEXT_PYTHON_HOME,
    RUNNER_CONTEXT_SANDBOX_BACKEND,
    RUNNER_CONTEXT_WORKSPACE_ROOT,
)
from cn.piflow.runtime import RunTrackingListener
from cn.piflow.runtime.logging import RunLogger
from cn.piflow.runtime.store.postgres import (
    PostgresConfig,
    PostgresRunStore,
    initialize_postgres_schema,
)


def _python_executable() -> Path:
    return Path(__import__("sys").executable).resolve()


def _pdf_text_skill_json() -> Path:
    return (
        Path(__file__).resolve().parent
        / "skills"
        / "skills-json"
        / "pdf_text_extract"
        / "skill.json"
    ).resolve()


def _pdf_metadata_skill_json() -> Path:
    return (
        Path(__file__).resolve().parent
        / "skills"
        / "skills-json"
        / "pdf_metadata_extract"
        / "skill.json"
    ).resolve()


def _pdf_metadata_to_csv_skill_json() -> Path:
    return (
        Path(__file__).resolve().parent
        / "skills"
        / "skills-json"
        / "pdf_metadata_to_csv"
        / "skill.json"
    ).resolve()


def _blank_line_clean_skill_json() -> Path:
    return (
        Path(__file__).resolve().parent
        / "skills"
        / "skills-json"
        / "DC1_Blank_Line_Clean"
        / "skill.json"
    ).resolve()


def _csv_formatter_skill_json() -> Path:
    return (
        Path(__file__).resolve().parent
        / "skills"
        / "skills-json"
        / "csv_formatter"
        / "skill.json"
    ).resolve()


def _workspace_root() -> Path:
    return (Path(__file__).resolve().parent / "workspace").resolve()


def _workspace_skill_json(skill_name: str) -> Path:
    skill_json = (
        _workspace_root()
        / "skills"
        / "skills-json"
        / skill_name
        / "skill.json"
    ).resolve()
    if not skill_json.exists():
        raise FileNotFoundError(f"workspace skill not found: {skill_json}")
    return skill_json


def _output_root() -> Path:
    return (Path(__file__).resolve().parent / "output").resolve()


def _skip_if_command_dependencies_missing(python_executable: Path) -> None:
    dependency_check = subprocess.run(
        [str(python_executable), "-c", "import pandas; import pypdf"],
        capture_output=True,
        text=True,
        check=False,
    )
    if dependency_check.returncode != 0:
        pytest.skip("pandas or pypdf is not installed in the configured command python")


def test_source_file_stop_feeds_pdf_text_extract() -> None:
    python_executable = _python_executable()
    dependency_check = subprocess.run(
        [str(python_executable), "-c", "import pypdf"],
        capture_output=True,
        text=True,
        check=False,
    )
    if dependency_check.returncode != 0:
        pytest.skip("pypdf is not installed in the configured command python")

    pdf_path = (Path(__file__).resolve().parent / "data" / "Akcay.pdf").resolve()
    skill_json = _pdf_text_skill_json()
    workspace = _workspace_root()
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    output_dir = _output_root()
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_output = output_dir / "pdf_text_extracd.txt"

    flow_data = {
        "flow": {
            "uuid": "flow-source-pdf-text-extract-001",
            "name": "source-pdf-text-extract-flow",
            "runMode": "RUN",
            "stops": [
                {
                    "uuid": "source-001",
                    "name": "SourceFile",
                    "bundle": "cn.piflow.engine.local.source_file_stop.SourceFileStop",
                    "properties": {
                        "input_file_path": str(pdf_path),
                    },
                },
                {
                    "uuid": "extract-001",
                    "name": "PdfTextExtract",
                    "bundle": str(skill_json),
                    "properties": {
                        "pages": "",
                    },
                },
                {
                    "uuid": "save-001",
                    "name": "SaveText",
                    "bundle": "cn.piflow.engine.local.file_save_stop.FileSaveStop",
                    "properties": {
                        "absolute_path": str(saved_output),
                        "overwrite": True,
                    },
                },
            ],
            "paths": [
                {
                    "from": "source-001",
                    "outport": "input_file_path",
                    "inport": "input_path",
                    "to": "extract-001",
                },
                {
                    "from": "extract-001",
                    "outport": "output_path",
                    "inport": "",
                    "to": "save-001",
                }
            ],
        }
    }

    flow = FlowBean.from_dict(flow_data).construct_flow()
    runner = (
        Runner.create()
        .bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace))
        .bind(RUNNER_CONTEXT_PYTHON_HOME, str(python_executable))
    )
    process = runner.start(flow)
    process.await_termination()

    extracted_files = list(workspace.rglob("extracted_text.txt"))
    assert len(extracted_files) == 1
    assert extracted_files[0].read_text(encoding="utf-8").strip() != ""
    assert saved_output.exists()
    assert saved_output.read_text(encoding="utf-8").strip() != ""

    execution_meta_files = list(workspace.rglob("execution.json"))
    assert len(execution_meta_files) == 1
    execution_meta = json.loads(execution_meta_files[0].read_text(encoding="utf-8"))
    assert execution_meta["resolved_values"]["input_path"] == str(pdf_path)
    assert execution_meta["resolved_values"]["output_path"] == str(extracted_files[0])


def test_source_pdf_metadata_to_csv_clean_and_save() -> None:
    python_executable = _python_executable()
    _skip_if_command_dependencies_missing(python_executable)

    pdf_path = "/data/Akcay.pdf"
    workspace = _workspace_root()
    workspace.mkdir(parents=True, exist_ok=True)
    workspace_data_pdf = workspace / "data" / "Akcay.pdf"
    workspace_data_pdf.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve().parent / "data" / "Akcay.pdf", workspace_data_pdf)
    pdf_metadata_skill_json = _workspace_skill_json("pdf_metadata_extract")
    pdf_metadata_to_csv_skill_json = _workspace_skill_json("pdf_metadata_to_csv")
    blank_line_clean_skill_json = _workspace_skill_json("DC1_Blank_Line_Clean")

    output_dir = _output_root()
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_output = output_dir / "pdf_metadata_cleaned.csv"

    flow_data = {
        "flow": {
            "uuid": "flow-source-pdf-metadata-clean-save-001",
            "name": "source-pdf-metadata-clean-save-flow",
            "runMode": "RUN",
            "stops": [
                {
                    "uuid": "source-001",
                    "name": "SourceFile",
                    "bundle": "cn.piflow.engine.local.source_file_stop.SourceFileStop",
                    "properties": {
                        "file_path": str(pdf_path),
                    },
                },
                {
                    "uuid": "metadata-001",
                    "name": "PdfMetadataExtract",
                    "bundle": str(pdf_metadata_skill_json),
                    "properties": {},
                },
                {
                    "uuid": "to-csv-001",
                    "name": "PdfMetadataToCsv",
                    "bundle": str(pdf_metadata_to_csv_skill_json),
                    "properties": {},
                },
                {
                    "uuid": "clean-001",
                    "name": "BlankLineClean",
                    "bundle": str(blank_line_clean_skill_json),
                    "properties": {},
                },
                {
                    "uuid": "save-001",
                    "name": "SaveCsv",
                    "bundle": "cn.piflow.engine.local.file_save_stop.FileSaveStop",
                    "properties": {
                        "absolute_path": str(saved_output),
                        "overwrite": True,
                    },
                },
            ],
            "paths": [
                {
                    "from": "source-001",
                    "outport": "output",
                    "inport": "input_path",
                    "to": "metadata-001",
                },
                {
                    "from": "metadata-001",
                    "outport": "output_path",
                    "inport": "metadata_path",
                    "to": "to-csv-001",
                },
                {
                    "from": "to-csv-001",
                    "outport": "output_path",
                    "inport": "input",
                    "to": "clean-001",
                },
                {
                    "from": "clean-001",
                    "outport": "output",
                    "inport": "",
                    "to": "save-001",
                },
            ],
        }
    }

    flow = FlowBean.from_dict(flow_data).construct_flow()
    connection = PostgresConfig.from_env().connect()
    initialize_postgres_schema(connection)
    store = PostgresRunStore(connection=connection)
    runner = (
        Runner.create()
        .bind(RUNNER_CONTEXT_SANDBOX_BACKEND, "docker")
        .bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace))
        .bind(RUNNER_CONTEXT_PYTHON_HOME, str(python_executable))
    )
    runner.add_listener(
        RunTrackingListener(
            run_store=store,
            run_logger=RunLogger(workspace),
        )
    )

    try:
        process = runner.start(flow)
        process.await_termination()
    finally:
        store.close()

    metadata_files = list(workspace.rglob("metadata.json"))
    csv_files = list(workspace.rglob("metadata.csv"))
    cleaned_files = list(workspace.rglob("cleaned_output.csv"))

    assert len(metadata_files) == 1
    assert len(csv_files) == 1
    assert len(cleaned_files) == 1
    assert saved_output.exists()
    assert saved_output.read_text(encoding="utf-8").strip() != ""


def test_source_file_csv_formatter_and_save_csv() -> None:
    python_executable = _python_executable()
    # dependency_check = subprocess.run(
    #     [str(python_executable), "-c", "import pandas; import data_juicer"],
    #     capture_output=True,
    #     text=True,
    #     check=False,
    # )
    # if dependency_check.returncode != 0:
    #     pytest.skip("pandas or data_juicer is not installed in the configured command python")

    workspace = _workspace_root()
    # if workspace.exists():
    #     shutil.rmtree(workspace)
    # workspace.mkdir(parents=True, exist_ok=True)

    source_csv = workspace / "data" / "input.csv"
    source_csv.parent.mkdir(parents=True, exist_ok=True)
    source_csv.write_text("text\nhello\nworld\n", encoding="utf-8")

    output_dir = _output_root()
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_output = output_dir / "csv_formatter_saved.jsonl"

    flow_data = {
        "flow": {
            "uuid": "flow-source-csv-formatter-save-001",
            "name": "source-csv-formatter-save-flow",
            "runMode": "RUN",
            "stops": [
                {
                    "uuid": "source-001",
                    "name": "SourceFile",
                    "bundle": "cn.piflow.engine.local.source_file_stop.SourceFileStop",
                    "properties": {
                        "file_path": "/data/input.csv",
                    },
                },
                {
                    "uuid": "csv-001",
                    "name": "csvformatter",
                    "bundle": str(_csv_formatter_skill_json()),
                    "properties": {
                        "add_suffix": False,
                        "encoding": "utf-8",
                    },
                },
                {
                    "uuid": "save-001",
                    "name": "SaveCsv",
                    "bundle": "cn.piflow.engine.local.file_save_stop.FileSaveStop",
                    "properties": {
                        "absolute_path": str(saved_output),
                        "overwrite": True,
                    },
                },
            ],
            "paths": [
                {
                    "from": "source-001",
                    "outport": "output",
                    "inport": "input_path",
                    "to": "csv-001",
                },
                {
                    "from": "csv-001",
                    "outport": "output_path",
                    "inport": "",
                    "to": "save-001",
                },
            ],
        }
    }

    flow = FlowBean.from_dict(flow_data).construct_flow()
    runner = (
        Runner.create()
        .bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace))
        .bind(RUNNER_CONTEXT_PYTHON_HOME, str(python_executable))
    )
    process = runner.start(flow)
    process.await_termination()

    formatted_files = list(workspace.rglob("csv_formatter_output.jsonl"))
    assert len(formatted_files) == 1
    assert formatted_files[0].read_text(encoding="utf-8").strip() != ""
    assert saved_output.exists()
    assert saved_output.read_text(encoding="utf-8").strip() != ""
