import logging

from enums.workflow_template_enums import TEMPLATE_TAG_VALUES, TemplatePublisher
from runtime.piflow_adapter import submit_frontend_dag
from runtime.workflow_template_manager import (
    delete_workflow_template_by_template_id,
    get_workflow_field_count,
    get_workflow_template_by_template_id,
    get_workflow_template_for_run,
    insert_workflow_template,
    list_workflow_template_by_condition, update_workflow_template,
)
from services.dag_panel_service import get_panel_dag_json

log = logging.getLogger("flow.workflow_template_service")

def save_workflow_template(
        user_id: str,
        user_name: str,
        template_name: str,
        description: str,
        dag_task_id: str,
        template_json: dict,
        disciplinary_field: str,
        tags: list,
        version: str,
        db_id: int = None,) -> dict:
    if template_name == "" or template_name is None or user_id == "" or user_id is None :
        raise ValueError("template_name and user_id is required")
    publisher = TemplatePublisher.PERSONAL
    valid_tags = [t for t in (tags or []) if t in TEMPLATE_TAG_VALUES]

    if db_id is None or db_id <= 0:
    # 如果task_id不为空，则需要去查dag_definition表
        if dag_task_id != "" and dag_task_id is not None:
            definition_json = get_panel_dag_json(
                create_user_id=user_id,
                dag_task_id=dag_task_id,
            )
            # 如果definition_json为空，则说明改任务没有对应的dag_definition，或该任务不是用户创建，需要抛出异常
            if definition_json == "" or definition_json is None:
                raise ValueError(f"task_id not found or not owned by user: {dag_task_id}")
            elif template_json == "" or template_json == {} or template_json is None:
                template_json = definition_json

        result = insert_workflow_template(user_id, user_name, template_name, description, template_json, disciplinary_field, publisher, valid_tags, version)
    else:
        result = update_workflow_template(db_id, user_id, user_name, template_name, description, disciplinary_field, publisher, valid_tags, version)
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


def run_workflow_template(user_id: str, template_id: str) -> dict:
    if not template_id or not user_id:
        raise ValueError("template_id and user_id is required")

    template = get_workflow_template_for_run(template_id)
    if not template:
        raise ValueError(f"workflow template not found: {template_id}")

    if template.get("is_deleted") == 1:
        raise ValueError(f"workflow template is deleted: {template_id}")

    publisher = template.get("publisher")
    author_id = template.get("author_id")

    if publisher == TemplatePublisher.PERSONAL.value:
        if author_id != user_id:
            raise PermissionError("no permission to run this workflow template")
    elif publisher in (
        TemplatePublisher.ORG_SHARED.value,
        TemplatePublisher.OFFICIAL_COMMUNITY.value,
    ):
        pass
    else:
        raise PermissionError(f"unsupported publisher: {publisher}")

    template_json = template.get("template_json")
    if not template_json:
        raise ValueError(f"workflow template json is empty: {template_id}")

    process = submit_frontend_dag(
        definition_json=template_json,
        user_id=user_id,
    )

    return {
        "dag_task_id": template_id,
        "process_id": process.pid(),
        "status": "SUBMITTED",
    }
