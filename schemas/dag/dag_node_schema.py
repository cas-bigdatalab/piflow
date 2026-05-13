from datetime import datetime
from typing import Optional

from schemas.dag.dag_node_input_param import DagNodeInputParamSet
from schemas.dag.dag_skill_schema import DagSkill


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