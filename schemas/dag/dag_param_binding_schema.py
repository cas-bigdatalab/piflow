from datetime import datetime

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
