from datetime import datetime

class DagTask:
    def __init__(
        self,
        dag_task_id: str,
        dag_task_name: str,
        description: str = None,
        message_id: str = None,
        create_user_id: str = None,
        db_id: int = None,
        is_deleted: int = 0,
        create_time: datetime = None,
        update_time: datetime = None,
        dag_task_type: int = 0,
    ):
        self.id = db_id
        self.dag_task_id = dag_task_id
        self.dag_task_name = dag_task_name
        self.message_id = message_id
        self.description = description
        self.create_user_id = create_user_id
        self.is_deleted = is_deleted
        self.create_time = create_time
        self.update_time = update_time
        self.dag_task_type = dag_task_type

    def to_json(self) -> dict:
        d: Dict[str, Any] = {
            "task_id": self.dag_task_id,
            "task_name": self.dag_task_name,
        }
        if self.description is not None:
            d["description"] = self.description
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.create_user_id is not None:
            d["create_user_id"] = self.create_user_id
        return d