from typing import Any, Dict


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