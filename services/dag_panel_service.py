from runtime.dag_manager import list_dag_tasks


def get_user_dag_tasks(
    create_user_id: str,
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
) -> dict:
    result = list_dag_tasks(
        create_user_id=create_user_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
    )
    # result["data"] = [t.to_json() for t in result["data"]]
    return result
