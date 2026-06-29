from __future__ import annotations

from pathlib import Path

from cn.piflow.core.artifact import FileArtifact
from cn.piflow.core.stream_impl import JobInputStreamImpl
from cn.piflow.engine.local.command_invocation_parser import CommandInvocationParser
from cn.piflow.engine.local.spec import CommandSpec


def _csv_formatter_spec() -> CommandSpec:
    return CommandSpec.from_dict(
        {
            "name": "csv_formatter",
            "version": "1.0.0",
            "description": "CSV formatter",
            "language": "python",
            "script_path": "scripts/run_csv_formatter.py",
            "entrypoint": "python scripts/run_csv_formatter.py",
            "input_params": [
                {
                    "name": "input_path",
                    "role": "input_data",
                    "type": "string",
                    "required": True,
                    "description": "input csv path",
                },
                {
                    "name": "output_path",
                    "role": "output_data",
                    "type": "string",
                    "required": True,
                    "description": "output jsonl path",
                },
                {
                    "name": "text_keys",
                    "role": "data",
                    "type": "list",
                    "required": False,
                    "description": "text key list",
                    "default": "['text']",
                },
                {
                    "name": "add_suffix",
                    "role": "data",
                    "type": "bool",
                    "required": False,
                    "description": "append suffix info",
                    "default": False,
                },
                {
                    "name": "num_proc",
                    "role": "data",
                    "type": "int",
                    "required": False,
                    "description": "parallel workers",
                    "default": 1,
                },
                {
                    "name": "encoding",
                    "role": "data",
                    "type": "string",
                    "required": False,
                    "description": "csv encoding",
                    "default": "utf-8",
                },
            ],
            "output_params": [
                {
                    "name": "output_path",
                    "role": "output_data",
                    "type": "jsonl_file",
                    "default": "csv_formatter_output.jsonl",
                    "description": "formatted jsonl file",
                }
            ],
            "command_template": [
                "python",
                "{script_path}",
                "--input_path",
                "{input_path}",
                "--output_path",
                "{output_path}",
                "--text_keys",
                "{text_keys}",
                "--add_suffix",
                "{add_suffix}",
                "--num_proc",
                "{num_proc}",
                "--encoding",
                "{encoding}",
            ],
        },
        base_dir=Path("/tmp/csv_formatter"),
        source="tests://csv_formatter",
    )


def test_command_invocation_parser_fills_defaults_for_csv_formatter(tmp_path: Path) -> None:
    parser = CommandInvocationParser(_csv_formatter_spec())
    inputs = JobInputStreamImpl(
        inputs={"input_path": FileArtifact(path=str(tmp_path / "input.csv"))}
    )

    invocation = parser.parse(inputs, tmp_path, properties={})

    expected_script_path = str(
        (Path("/tmp/csv_formatter") / "scripts/run_csv_formatter.py").resolve()
    )
    expected_output_path = str((tmp_path / "output" / "csv_formatter_output.jsonl").resolve())

    assert invocation.command == [
        "python",
        expected_script_path,
        "--input_path",
        str(tmp_path / "input.csv"),
        "--output_path",
        expected_output_path,
        "--text_keys",
        "['text']",
        "--add_suffix",
        "False",
        "--num_proc",
        "1",
        "--encoding",
        "utf-8",
    ]
    assert invocation.resolved_values["input_path"] == str(tmp_path / "input.csv")
    assert invocation.resolved_values["output_path"] == expected_output_path
    assert invocation.runtime_properties == {
        "text_keys": "['text']",
        "add_suffix": "False",
        "num_proc": "1",
        "encoding": "utf-8",
    }
    assert invocation.output_files == {"output_path": expected_output_path}


def test_command_invocation_parser_skips_missing_optional_runtime_parameter(tmp_path: Path) -> None:
    spec = CommandSpec.from_dict(
        {
            "name": "csv_formatter",
            "script_path": "scripts/run_csv_formatter.py",
            "input_params": [
                {
                    "name": "input_path",
                    "role": "input_data",
                    "required": True,
                },
                {
                    "name": "output_path",
                    "role": "output_data",
                    "required": True,
                },
                {
                    "name": "num_proc",
                    "role": "data",
                    "type": "int",
                    "required": False,
                },
            ],
            "output_params": [
                {
                    "name": "output_path",
                    "role": "output_data",
                    "type": "jsonl_file",
                    "default": "csv_formatter_output.jsonl",
                }
            ],
            "command_template": [
                "python",
                "{script_path}",
                "--input_path",
                "{input_path}",
                "--output_path",
                "{output_path}",
                "--num_proc",
                "{num_proc}",
            ],
        },
        base_dir=tmp_path,
    )
    parser = CommandInvocationParser(spec)
    inputs = JobInputStreamImpl(
        inputs={"input_path": FileArtifact(path=str(tmp_path / "input.csv"))}
    )

    invocation = parser.parse(inputs, tmp_path, properties={})

    assert invocation.command == [
        "python",
        str((tmp_path / "scripts/run_csv_formatter.py").resolve()),
        "--input_path",
        str(tmp_path / "input.csv"),
        "--output_path",
        str((tmp_path / "output" / "csv_formatter_output.jsonl").resolve()),
    ]
    assert "num_proc" not in invocation.resolved_values
    assert "num_proc" not in invocation.runtime_properties
