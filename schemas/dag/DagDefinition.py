from pydantic import BaseModel

class DagDefinition(BaseModel):
    dsl_version:str
    task:dict
    nodes:list
    edges:list
    bindings:list