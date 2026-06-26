from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from piflow_engine.cn.piflow.core.flow import Flow, FlowImpl
from piflow_engine.cn.piflow.core.path import Path
from piflow_engine.cn.piflow.core.path_bean import PathBean
from piflow_engine.cn.piflow.core.stop_bean import StopBean


@dataclass
class FlowBean:
    uuid: str = ""
    name: str = ""
    run_mode: str = "RUN" # DEBUG
    stops: list[StopBean] = field(default_factory=list)
    paths: list[PathBean] = field(default_factory=list)
    environment_variable: dict[str, Any] = field(default_factory=dict)
    flow_json: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FlowBean":
        flow_map = dict(data.get("flow", {}))
        bean = cls(
            uuid=str(flow_map.get("uuid", "")),
            name=str(flow_map.get("name", "")),
            run_mode=str(flow_map.get("runMode", "RUN")),
            environment_variable=dict(flow_map.get("environmentVariable", {})),
            flow_json=json.dumps(data, ensure_ascii=False, indent=2),
        )

        stops_data = list(flow_map.get("stops", []))
        if bean.environment_variable:
            stops_data = [
                bean._replace_environment_variables_in_stop(stop_data)
                for stop_data in stops_data
            ]

        bean.stops = [StopBean.from_dict(bean.name, stop_data) for stop_data in stops_data]
        bean.paths = [PathBean.from_dict(path_data) for path_data in flow_map.get("paths", [])]
        return bean

    def construct_flow(self) -> Flow:
        flow = FlowImpl(
            name=self.name,
            uuid=self.uuid,
            run_mode=self.run_mode,
            flow_json=self.flow_json,
        )

        for stop_bean in self.stops:
            flow.add_stop(stop_bean.uuid or stop_bean.name, stop_bean.construct_stop())

        for path_bean in self.paths:
            path = Path.from_(path_bean.from_stop).via(
                path_bean.out_port, path_bean.in_port
            ).to(path_bean.to_stop)
            flow.add_path(path)

        return flow

    def _replace_environment_variables_in_stop(
        self, stop_data: dict[str, Any]
    ) -> dict[str, Any]:
        result = dict(stop_data)
        properties = dict(result.get("properties", {}))
        pattern = re.compile(r"\$\{+[^}]*\}")

        for key, value in list(properties.items()):
            if not isinstance(value, str):
                continue
            replaced = value
            for item in pattern.findall(value):
                replaced = replaced.replace(
                    item, str(self.environment_variable.get(item, item))
                )
            properties[key] = replaced

        result["properties"] = properties
        return result
