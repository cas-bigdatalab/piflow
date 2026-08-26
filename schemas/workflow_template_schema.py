from typing import Optional

from pydantic import BaseModel


class WorkflowTemplateCreateRequest(BaseModel):
    template_name: str
    description: str = ""
    template_json: dict
    disciplinary_field: Optional[str] = "基础"
    tags: Optional[list] = None
    version: str = "1.0.0"
