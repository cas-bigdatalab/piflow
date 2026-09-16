from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from runtime.piflow_adapter import submit_frontend_dag

from .config import ChemicalConfig
from .dag_scheduler import schedule_chemical_dag
from .resource_listener import ChemicalResourceTrackingListener


def _default_config_path() -> Path:
    env_path = os.getenv("CHEMICAL_CONFIG_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    package_dir = Path(__file__).resolve().parent
    configured = package_dir / "config.yaml"
    return configured if configured.exists() else package_dir / "config.example.yaml"


def submit_chemical_dag(
    definition_json: dict[str, Any],
    *,
    config: ChemicalConfig | None = None,
    config_path: str | Path | None = None,
    workspace_root: str | Path | None = None,
    user_id: str | None = None,
    python_home: str | None = None,
) -> Any:
    """Schedule a Chemical DAG and submit it to the local PiFlow runner."""
    chemical_config = config or ChemicalConfig.from_file(
        config_path or _default_config_path()
    )
    plan = schedule_chemical_dag(definition_json, config=chemical_config)
    runtime_metadata = {
        decision.node_id: {
            "resource_node_name": decision.resource_node_name,
            "required_software": decision.required_software,
            "resource_bindings": decision.resource_bindings,
            "execution_node_name": decision.execution_node_name,
            "transformed": decision.transformed,
        }
        for decision in plan.decisions
        if decision.required_software and decision.resource_node_name
    }

    return submit_frontend_dag(
        definition_json=plan.dag_definition,
        workspace_root=workspace_root,
        user_id=user_id,
        python_home=python_home,
        additional_listeners=[ChemicalResourceTrackingListener()],
        stop_runtime_metadata=runtime_metadata,
    )
