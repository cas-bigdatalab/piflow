from typing import List, Optional

from schemas.dag.dag_edge_schema import DagEdge
from schemas.dag.dag_node_schema import DagNode
from schemas.dag.dag_param_binding_schema import DagParamBinding
from schemas.dag.dag_task_schema import DagTask


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