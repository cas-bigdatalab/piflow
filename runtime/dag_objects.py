from datetime import datetime
from typing import Any, Dict, List, Optional, Union


class DagNodeReferenceParam:
    def __init__(self, param_name: str, binding_id: str):
        self.param_name = param_name
        self.value_mode = "reference"
        self.binding_id = binding_id

    def to_dict(self) -> dict:
        return {
            "param_name": self.param_name,
            "value_mode": self.value_mode,
            "binding_id": self.binding_id,
        }


class DagNodeManualParam:
    def __init__(
        self,
        param_name: str,
        param_type: str,
        param_value: str,
        value_source: str = "local_file",
    ):
        self.param_name = param_name
        self.value_mode = "manual"
        self.param_type = param_type
        self.value_source = value_source
        self.param_value = param_value

    def to_dict(self) -> dict:
        return {
            "param_name": self.param_name,
            "value_mode": self.value_mode,
            "param_type": self.param_type,
            "value_source": self.value_source,
            "param_value": self.param_value,
        }


class DagNodeInputParamSet:
    def __init__(self):
        self.params: List[Union[DagNodeReferenceParam, DagNodeManualParam]] = []

    def add_param(self, param: Union[DagNodeReferenceParam, DagNodeManualParam]):
        self.params.append(param)

    def to_list(self) -> list:
        return [p.to_dict() for p in self.params]

    def to_json_dict(self) -> dict:
        return {"input_params": self.to_list()}


class DagTask:
    def __init__(
        self,
        dag_task_id: str,
        dag_task_name: str,
        description: str = None,
        message_id: str = None,
        create_user: str = None,
        db_id: int = None,
        is_deleted: int = 0,
        create_time: datetime = None,
        update_time: datetime = None,
    ):
        self.id = db_id
        self.dag_task_id = dag_task_id
        self.dag_task_name = dag_task_name
        self.message_id = message_id
        self.description = description
        self.create_user = create_user
        self.is_deleted = is_deleted
        self.create_time = create_time
        self.update_time = update_time

    def to_json(self) -> dict:
        d: Dict[str, Any] = {
            "task_id": self.dag_task_id,
            "task_name": self.dag_task_name,
        }
        if self.description is not None:
            d["description"] = self.description
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.create_user is not None:
            d["create_user"] = self.create_user
        return d


class DagSkill:
    def __init__(
        self,
        skill_id: str,
        skill_name: str,
        version: str = "1.0.0",
        description: str = None,
        file_path: str = None,
        input_params: dict = None,
        output_params: dict = None,
        skill_type: str = None,
        language: str = None,
        command: str = None,
        icon_path: str = None,
        db_id: int = None,
        create_time: datetime = None,
        update_time: datetime = None,
        is_deleted: int = 0,
    ):
        self.id = db_id
        self.skill_id = skill_id
        self.skill_name = skill_name
        self.version = version
        self.description = description
        self.file_path = file_path
        self.input_params = input_params or {}
        self.output_params = output_params or {}
        self.skill_type = skill_type
        self.language = language
        self.command = command
        self.icon_path = icon_path
        self.create_time = create_time
        self.update_time = update_time
        self.is_deleted = is_deleted

    def to_json(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "version": self.version,
        }


class DagNode:
    def __init__(
        self,
        node_id: str,
        node_name: str,
        skill_id: str,
        node_type: str = "default",
        position_x: float = 0,
        position_y: float = 0,
        input_params: Optional[DagNodeInputParamSet] = None,
        skill: Optional[DagSkill] = None,
        db_id: int = None,
        dag_task_id: str = None,
        update_time: datetime = None,
    ):
        self.id = db_id
        self.node_id = node_id
        self.dag_task_id = dag_task_id
        self.skill_id = skill_id
        self.node_name = node_name
        self.skill = skill
        self.node_type = node_type
        self.position_x = position_x
        self.position_y = position_y
        self.input_params = input_params or DagNodeInputParamSet()
        self.update_time = update_time

    def to_json(self) -> dict:
        skill_json = self.skill.to_json() if self.skill else {
            "skill_id": self.skill_id,
            "skill_name": self.skill_id,
            "version": "1.0.0",
        }
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": self.node_type,
            "skill": skill_json,
            "position": {"x": self.position_x, "y": self.position_y},
            "input_params": self.input_params.to_list(),
        }


class DagEdge:
    def __init__(
        self,
        edge_id: str,
        from_node_id: str,
        to_node_id: str,
        from_port: str = None,
        to_port: str = None,
        db_id: int = None,
        dag_task_id: str = None,
    ):
        self.id = db_id
        self.edge_id = edge_id
        self.dag_task_id = dag_task_id
        self.from_node_id = from_node_id
        self.to_node_id = to_node_id
        self.from_port = from_port
        self.to_port = to_port

    def to_json(self) -> dict:
        d: Dict[str, Any] = {
            "edge_id": self.edge_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
        }
        if self.from_port is not None:
            d["from_port"] = self.from_port
        if self.to_port is not None:
            d["to_port"] = self.to_port
        return d


class DagParamBinding:
    def __init__(
        self,
        binding_id: str,
        from_node_id: str,
        from_param_name: str,
        to_node_id: str,
        to_param_name: str,
        db_id: int = None,
        dag_task_id: str = None,
        create_time: datetime = None,
    ):
        self.id = db_id
        self.binding_id = binding_id
        self.dag_task_id = dag_task_id
        self.from_node_id = from_node_id
        self.from_param_name = from_param_name
        self.to_node_id = to_node_id
        self.to_param_name = to_param_name
        self.create_time = create_time

    def to_json(self) -> dict:
        return {
            "binding_id": self.binding_id,
            "from_node_id": self.from_node_id,
            "from_param_name": self.from_param_name,
            "to_node_id": self.to_node_id,
            "to_param_name": self.to_param_name,
        }


class DagObs:
    def __init__(self, task: DagTask, nodes: Optional[List[DagNode]] = None, edges: Optional[List[DagEdge]] = None, bindings: Optional[List[DagParamBinding]] = None):
        self.task = task
        self.nodes: List[DagNode] = nodes
        self.edges: List[DagEdge] = edges
        self.bindings: List[DagParamBinding] = bindings

    def add_node(self, node: DagNode):
        self.nodes.append(node)

    def add_edge(self, edge: DagEdge):
        self.edges.append(edge)

    def add_binding(self, binding: DagParamBinding):
        self.bindings.append(binding)

    def to_json(self) -> dict:
        return {
            "task": self.task.to_json(),
            "nodes": [n.to_json() for n in self.nodes],
            "edges": [e.to_json() for e in self.edges],
            "bindings": [b.to_json() for b in self.bindings],
        }
