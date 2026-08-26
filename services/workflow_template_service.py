import logging

from enums.workflow_template_enums import TEMPLATE_TAG_VALUES, TemplatePublisher
from runtime.workflow_template_manager import (
    delete_workflow_template_by_template_id,
    get_workflow_field_count,
    get_workflow_template_by_template_id,
    insert_workflow_template,
    list_workflow_template_by_condition,
)

log = logging.getLogger("flow.workflow_template_service")

def save_workflow_template(
        user_id: str,
        user_name: str,
        template_name: str,
        description: str,
        template_json: dict,
        disciplinary_field: str,
        tags: list,
        version: str) -> dict:
    if template_name == "" or template_name is None or user_id == "" or user_id is None :
        raise ValueError("template_name and user_id is required")
    publisher = TemplatePublisher.PERSONAL
    valid_tags = [t for t in (tags or []) if t in TEMPLATE_TAG_VALUES]
    result = insert_workflow_template(user_id, user_name, template_name, description, template_json, disciplinary_field, publisher, valid_tags, version)
    return result

def list_workflow_templates_by_params(
        page: int,
        page_size: int,
        keyword: str = None,
        disciplinary_field: str = None,
        publisher: str = None,
        user_id: str = None) -> dict:
    return list_workflow_template_by_condition(
        page=page,
        page_size=page_size,
        keyword=keyword or None,
        disciplinary_field=disciplinary_field or None,
        publisher=publisher or None,
        user_id=user_id,
    )

def get_workflow_template_fields_info(user_id: str = None) -> list:
    return get_workflow_field_count(user_id)

def get_workflow_template_detail_info(template_id: str, user_id: str = None):
    row = get_workflow_template_by_template_id(template_id, user_id)
    if not row:
        return None
    return dict(row)

def remove_workflow_template(template_id: str, user_id: str) -> bool:
    if template_id == "" or template_id is None or user_id == "" or user_id is None:
        raise ValueError("template_id and user_id is required")
    return delete_workflow_template_by_template_id(template_id, user_id)
