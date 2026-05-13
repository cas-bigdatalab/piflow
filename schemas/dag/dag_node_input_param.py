from typing import List, Union

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
