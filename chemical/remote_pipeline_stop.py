"""Chemical remote pipeline stop with dynamic file inputs and outputs."""

from __future__ import annotations

import copy
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from piflow_engine.cn.piflow.core.artifact import Artifact, FileArtifact, RemoteFileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.runtime.logging.path_utils import safe_name


CHEMICAL_FILE_SOURCE_BUNDLE = "chemical.file_source_stop.ChemicalFileSourceStop"
DEFAULT_OUTPUT_PORT = "output"
RUNNER_CONTEXT_WORKSPACE_ROOT = "local.workspace_root"


class RemoteExecutionGateway(Protocol):
    def submit_dag(self, dag_definition_json: str): ...

    def get_run_status(self, run_id: str): ...

    def get_run_result_meta(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
    ): ...

    def download_result(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
        target_path: str | Path,
    ) -> str: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class _InputSpec:
    port: str
    path: str
    target_server: str


@dataclass(frozen=True)
class _ResultSpec:
    port: str
    node_id: str
    output_name: str


class ChemicalRemotePipelineStop(ConfigurableStop):
    """Build and run a chemical DAG on a remote PiFlow server.

    The stop turns every incoming file artifact into a remote
    ChemicalFileSourceStop that points back to the local PiFlow file server,
    submits the generated frontend DAG to ``target_server``, then downloads
    configured result ports from that remote run.
    """

    author_email = ""
    description = "Chemical remote pipeline stop with dynamic file inputs and outputs."
    inport_list: list[str] = []
    outport_list: list[str] = []

    client_factory = None

    def __init__(self) -> None:
        super().__init__()
        self.node_definition_json = ""
        self.target_server = ""
        self.local_server = ""
        self.poll_interval_seconds = 1.0
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        raw_definition = properties.get("node_definition_json", "")
        self.node_definition_json = _normalize_optional_json(raw_definition)
        if not self.node_definition_json:
            raise ValueError("node_definition_json is required")
        self._sync_port_contract(self._load_node_definition())

        self.target_server = _read_server(
            properties,
            "target_server",
            aliases=("remote_grpc_target", "target_grpc_server"),
        )
        self.local_server = _read_local_server(properties)
        self.poll_interval_seconds = _read_poll_interval(
            properties.get("poll_interval_seconds", 1.0)
        )

    def _sync_port_contract(self, definition: dict[str, Any]) -> None:
        """Expose exactly the ports declared by the configured node JSON."""
        if "nodes" in definition:
            nodes = definition.get("nodes", [])
            if not isinstance(nodes, list):
                raise ValueError("chemical remote dag 'nodes' must be a list")
            bindings = definition.get("bindings", [])
            if not isinstance(bindings, list):
                raise ValueError("chemical remote dag 'bindings' must be a list")
            incoming = {str(item.get("to_node_id", "")) for item in bindings}
            outgoing = {str(item.get("from_node_id", "")) for item in bindings}
            entry_nodes = [
                item for item in nodes
                if isinstance(item, dict)
                and str(item.get("node_id", "")) not in incoming
            ]
            terminal_nodes = [
                item for item in nodes
                if isinstance(item, dict)
                and str(item.get("node_id", "")) not in outgoing
            ]
            self.inport_list = _unique_param_names(
                param
                for node in entry_nodes
                for param in _external_input_params_for_entry_node(node)
            )
            self.outport_list = _unique_param_names(
                param
                for node in terminal_nodes
                for param in node.get("out_params", [])
            )
            return
        else:
            node = definition

        self.inport_list = _reference_param_names(node.get("input_params", []))
        self.outport_list = _param_names(node.get("out_params", []))

    def initialize(self, ctx: ProcessContext) -> None:
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, ".piflow/workspace")
        self._workspace_root = Path(str(workspace_root)).expanduser().resolve()
        self._workspace_root.mkdir(parents=True, exist_ok=True)

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        input_specs = self._collect_inputs(inputs)
        dag_definition = self._load_node_definition()
        dag, result_specs = self._build_dag(dag_definition, input_specs)
        dag_json = json.dumps(dag, ensure_ascii=False)

        client = self._create_client()
        try:
            submit_resp = client.submit_dag(dag_json)
            run_id = str(submit_resp.run_id)
            self._wait_for_success(client, run_id)
            for result_spec in result_specs:
                meta = client.get_run_result_meta(
                    run_id=run_id,
                    result_node_id=result_spec.node_id,
                    result_output_name=result_spec.output_name,
                )
                target_path = self._prepare_output_path(
                    ctx,
                    result_spec.port,
                    str(getattr(meta, "file_name", "") or f"{result_spec.port}.bin"),
                )
                local_path = client.download_result(
                    run_id=run_id,
                    result_node_id=result_spec.node_id,
                    result_output_name=result_spec.output_name,
                    target_path=target_path,
                )
                outputs.write(FileArtifact(path=str(local_path)), result_spec.port)
        finally:
            client.close()

    def _collect_inputs(self, inputs: JobInputStream) -> list[_InputSpec]:
        result: list[_InputSpec] = []
        for port in inputs.ports():
            if port not in self.inport_list:
                raise ValueError(
                    f"chemical remote pipeline input port '{port}' is not declared "
                    f"by node JSON: {self.inport_list}"
                )
            artifact = inputs.read(port)
            path = _artifact_path(artifact)
            target_server = (
                artifact.target_server
                if isinstance(artifact, RemoteFileArtifact) and artifact.target_server
                else self.local_server
            )
            result.append(_InputSpec(port=port, path=path, target_server=target_server))
        return result

    def _load_node_definition(self) -> dict[str, Any]:
        loaded = json.loads(self.node_definition_json)
        if not isinstance(loaded, dict):
            raise ValueError("chemical remote node json must decode to a json object")
        self._sync_port_contract(loaded)
        return loaded

    def _build_dag(
        self,
        definition: dict[str, Any],
        input_specs: list[_InputSpec],
    ) -> tuple[dict[str, Any], list[_ResultSpec]]:
        if "nodes" in definition:
            dag = copy.deepcopy(definition)
            _ensure_frontend_dag_defaults(dag)
            self._inject_inputs_into_dag(dag, input_specs)
            return dag, self._resolve_result_specs(dag, single_node=None)

        node = copy.deepcopy(definition)
        dag = {
            "task": {
                "dag_task_id": f"chemical-remote-{uuid.uuid4().hex}",
                "dag_task_name": str(node.get("node_name") or "chemical remote pipeline"),
            },
            "nodes": [],
            "bindings": [],
        }
        source_nodes, bindings = _build_source_nodes_for_single_node(node, input_specs)
        dag["nodes"].extend(source_nodes)
        dag["nodes"].append(node)
        dag["bindings"].extend(bindings)
        return dag, self._resolve_result_specs(dag, single_node=node)

    def _inject_inputs_into_dag(
        self,
        dag: dict[str, Any],
        input_specs: list[_InputSpec],
    ) -> None:
        nodes = _dag_nodes(dag)
        bindings = _dag_bindings(dag)

        source_nodes = [
            node for node in nodes
            if str(node.get("skill", {}).get("skill_id", "")) in {
                "piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop",
                CHEMICAL_FILE_SOURCE_BUNDLE,
            }
        ]
        if source_nodes:
            for node, input_spec in zip(source_nodes, input_specs):
                _replace_with_chemical_source(node, input_spec)
            return

        targets = _unbound_reference_inputs(dag)
        for index, input_spec in enumerate(input_specs):
            node_id = f"chemical-input-{index + 1}"
            nodes.append(_source_node(node_id, f"Chemical input {input_spec.port}", input_spec))
            to_node_id, to_param_name = targets[index] if index < len(targets) else ("", input_spec.port)
            if to_node_id:
                bindings.append(
                    _binding(
                        from_node_id=node_id,
                        to_node_id=to_node_id,
                        to_param_name=to_param_name,
                    )
                )

    def _resolve_result_specs(
        self,
        dag: dict[str, Any],
        *,
        single_node: dict[str, Any] | None,
    ) -> list[_ResultSpec]:
        if single_node is not None:
            node_id = str(single_node.get("node_id", ""))
            specs = [
                _ResultSpec(
                    port=str(param["param_name"]),
                    node_id=node_id,
                    output_name=str(param["param_name"]),
                )
                for param in single_node.get("out_params", [])
                if param.get("param_name")
            ]
            return specs or [_ResultSpec(DEFAULT_OUTPUT_PORT, node_id, "")]

        terminal_nodes = _terminal_nodes(dag)
        specs: list[_ResultSpec] = []
        used_ports: set[str] = set()
        for node in terminal_nodes:
            node_id = str(node.get("node_id", ""))
            out_params = [p for p in node.get("out_params", []) if p.get("param_name")]
            if not out_params:
                port = _unique_port(DEFAULT_OUTPUT_PORT, used_ports)
                specs.append(_ResultSpec(port=port, node_id=node_id, output_name=""))
                continue
            for param in out_params:
                output_name = str(param["param_name"])
                port = _unique_port(output_name, used_ports)
                specs.append(_ResultSpec(port=port, node_id=node_id, output_name=output_name))
        return specs or [_ResultSpec(DEFAULT_OUTPUT_PORT, "", "")]

    def _create_client(self) -> RemoteExecutionGateway:
        factory = getattr(self, "client_factory", None)
        if callable(factory):
            return factory(self)

        from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

        return RemoteExecutionClient(self.target_server)

    def _wait_for_success(self, client: RemoteExecutionGateway, run_id: str) -> None:
        while True:
            status_resp = client.get_run_status(run_id)
            status = str(status_resp.status or "")
            if status == "SUCCESS":
                return
            if status in {"FAILED", "CANCELLED"}:
                raise RuntimeError(f"remote chemical pipeline failed with status {status}: {status_resp.message}")
            time.sleep(self.poll_interval_seconds)

    def _prepare_output_path(self, ctx: JobContext, port: str, file_name: str) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        process_id = ctx.get_process_context().get_process().pid()
        stop_name = safe_name(ctx.get_stop_job().get_stop_name())
        job_id = ctx.get_stop_job().jid()
        output_dir = (
            self._workspace_root
            / process_id
            / f"{stop_name}_{job_id}_{uuid.uuid4().hex[:8]}"
            / "output"
            / safe_name(port)
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / (Path(file_name).name or "remote_result.bin")


def _build_source_nodes_for_single_node(
    node: dict[str, Any],
    input_specs: list[_InputSpec],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    reference_params = [
        str(param.get("param_name", ""))
        for param in node.get("input_params", [])
        if param.get("value_mode") == "reference" and param.get("param_name")
    ]
    source_nodes: list[dict[str, Any]] = []
    bindings: list[dict[str, str]] = []
    target_node_id = str(node.get("node_id", "chemical-target-node"))
    reference_param_names = set(reference_params)

    for index, input_spec in enumerate(input_specs):
        source_node_id = f"chemical-input-{index + 1}"
        source_nodes.append(_source_node(source_node_id, f"Chemical input {input_spec.port}", input_spec))
        if input_spec.port in reference_param_names:
            to_param_name = input_spec.port
        elif index < len(reference_params):
            to_param_name = reference_params[index]
        else:
            to_param_name = input_spec.port
        bindings.append(
            _binding(
                from_node_id=source_node_id,
                to_node_id=target_node_id,
                to_param_name=to_param_name,
            )
        )

    return source_nodes, bindings


def _source_node(node_id: str, node_name: str, input_spec: _InputSpec) -> dict[str, Any]:
    remote_ip, remote_port = _split_server(input_spec.target_server)
    return {
        "node_id": node_id,
        "node_name": node_name,
        "skill": {"skill_id": CHEMICAL_FILE_SOURCE_BUNDLE},
        "input_params": [
            {"param_name": "source_type", "value_mode": "manual", "param_value": "remote"},
            {"param_name": "remote_ip", "value_mode": "manual", "param_value": remote_ip},
            {"param_name": "remote_port", "value_mode": "manual", "param_value": remote_port},
            {"param_name": "remote_path", "value_mode": "manual", "param_value": input_spec.path},
        ],
        "out_params": [{"param_name": DEFAULT_OUTPUT_PORT, "param_type": "file"}],
    }


def _replace_with_chemical_source(node: dict[str, Any], input_spec: _InputSpec) -> None:
    replacement = _source_node(
        str(node.get("node_id", "")),
        str(node.get("node_name") or f"Chemical input {input_spec.port}"),
        input_spec,
    )
    node["skill"] = replacement["skill"]
    node["input_params"] = replacement["input_params"]
    node["out_params"] = replacement["out_params"]


def _external_input_params_for_entry_node(node: dict[str, Any]) -> list[dict[str, Any]]:
    input_params = node.get("input_params", [])
    if not isinstance(input_params, list):
        raise ValueError("node JSON parameter list must be a list")

    skill_id = str(node.get("skill", {}).get("skill_id", ""))
    if skill_id in {
        "piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop",
        CHEMICAL_FILE_SOURCE_BUNDLE,
    }:
        return [param for param in input_params if isinstance(param, dict)]

    return [
        param
        for param in input_params
        if isinstance(param, dict) and param.get("value_mode") == "reference"
    ]


def _binding(*, from_node_id: str, to_node_id: str, to_param_name: str) -> dict[str, str]:
    return {
        "binding_id": uuid.uuid4().hex[:16],
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "from_param_name": DEFAULT_OUTPUT_PORT,
        "to_param_name": to_param_name,
    }


def _ensure_frontend_dag_defaults(dag: dict[str, Any]) -> None:
    dag.setdefault("task", {})
    dag.setdefault("nodes", [])
    dag.setdefault("bindings", [])


def _dag_nodes(dag: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = dag.setdefault("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("chemical remote dag 'nodes' must be a list")
    return nodes


def _dag_bindings(dag: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = dag.setdefault("bindings", [])
    if not isinstance(bindings, list):
        raise ValueError("chemical remote dag 'bindings' must be a list")
    return bindings


def _unbound_reference_inputs(dag: dict[str, Any]) -> list[tuple[str, str]]:
    bound = {
        (str(binding.get("to_node_id", "")), str(binding.get("to_param_name", "")))
        for binding in _dag_bindings(dag)
    }
    targets: list[tuple[str, str]] = []
    for node in _dag_nodes(dag):
        node_id = str(node.get("node_id", ""))
        for param in node.get("input_params", []):
            param_name = str(param.get("param_name", ""))
            if param.get("value_mode") != "reference" or not param_name:
                continue
            if (node_id, param_name) not in bound:
                targets.append((node_id, param_name))
    return targets


def _terminal_nodes(dag: dict[str, Any]) -> list[dict[str, Any]]:
    outgoing = {str(binding.get("from_node_id", "")) for binding in _dag_bindings(dag)}
    terminals = [
        node for node in _dag_nodes(dag)
        if str(node.get("node_id", "")) not in outgoing
    ]
    return terminals


def _unique_port(port: str, used_ports: set[str]) -> str:
    base = safe_name(port or DEFAULT_OUTPUT_PORT)
    candidate = base
    index = 2
    while candidate in used_ports:
        candidate = f"{base}_{index}"
        index += 1
    used_ports.add(candidate)
    return candidate


def _artifact_path(artifact: Artifact) -> str:
    path = getattr(artifact, "path", "") or getattr(artifact, "value", "")
    text = str(path or "").strip()
    if not text:
        raise ValueError("chemical remote pipeline input artifact must contain a file path")
    return text


def _param_names(params: Any) -> list[str]:
    if not isinstance(params, list):
        raise ValueError("node JSON parameter list must be a list")
    names: list[str] = []
    for param in params:
        if not isinstance(param, dict) or not param.get("param_name"):
            continue
        name = str(param["param_name"])
        if name not in names:
            names.append(name)
    return names


def _reference_param_names(params: Any) -> list[str]:
    if not isinstance(params, list):
        raise ValueError("node JSON parameter list must be a list")
    return _unique_param_names(
        param
        for param in params
        if isinstance(param, dict) and param.get("value_mode") == "reference"
    )


def _unique_param_names(params: Any) -> list[str]:
    names: list[str] = []
    for param in params:
        if not isinstance(param, dict) or not param.get("param_name"):
            continue
        name = str(param["param_name"])
        if name not in names:
            names.append(name)
    return names


def _read_optional_string(
    properties: dict[str, Any],
    key: str,
    *,
    aliases: tuple[str, ...] = (),
) -> str:
    for candidate in (key, *aliases):
        if candidate not in properties:
            continue
        value = properties[candidate]
        if not isinstance(value, str):
            raise TypeError(f"chemical remote pipeline property '{key}' must be a string")
        return value.strip()
    return ""


def _read_server(
    properties: dict[str, Any],
    key: str,
    *,
    aliases: tuple[str, ...] = (),
) -> str:
    value = _read_optional_string(properties, key, aliases=aliases)
    if not value:
        raise ValueError(f"{key} is required")
    _split_server(value)
    return value


def _read_local_server(properties: dict[str, Any]) -> str:
    value = _read_optional_string(
        properties,
        "local_server",
        aliases=("local_grpc_target", "local_file_server"),
    )
    if value:
        _split_server(value)
        return value

    local_ip = _read_optional_string(properties, "local_ip")
    local_port = properties.get("local_port", properties.get("local_file_port", ""))
    if local_ip and local_port not in (None, ""):
        return f"{local_ip}:{_read_port(local_port)}"
    raise ValueError("local_server or local_ip/local_port is required")


def _split_server(value: str) -> tuple[str, int]:
    host, sep, port_text = value.rpartition(":")
    if not sep or not host.strip():
        raise ValueError(f"invalid server address: {value}")
    return host.strip(), _read_port(port_text)


def _read_port(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("port must be an integer")
    if isinstance(value, int):
        port = value
    elif isinstance(value, str) and value.strip().isdigit():
        port = int(value.strip())
    else:
        raise TypeError("port must be an integer")
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    return port


def _read_poll_interval(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise TypeError("poll_interval_seconds must be a number")
    interval = float(value)
    if interval <= 0:
        raise ValueError("poll_interval_seconds must be positive")
    return interval


def _normalize_optional_json(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, str):
        parsed = json.loads(value)
    elif isinstance(value, dict):
        parsed = value
    else:
        raise TypeError("node_definition_json must be a json string or object")
    if not isinstance(parsed, dict):
        raise ValueError("node_definition_json must decode to a json object")
    return json.dumps(parsed, ensure_ascii=False)
