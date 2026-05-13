from datetime import datetime

class DagSkill:
    def __init__(
        self,
        skill_id: str,
        skill_name: str,
        version: str = "1.0.0",
        description: str = None,
        file_path: str = None,
        input_params: dict = None,
        output_params: dict = None,
        skill_type: str = None,
        language: str = None,
        command: str = None,
        icon_path: str = None,
        db_id: int = None,
        create_time: datetime = None,
        update_time: datetime = None,
        is_deleted: int = 0,
    ):
        self.id = db_id
        self.skill_id = skill_id
        self.skill_name = skill_name
        self.version = version
        self.description = description
        self.file_path = file_path
        self.input_params = input_params or {}
        self.output_params = output_params or {}
        self.skill_type = skill_type
        self.language = language
        self.command = command
        self.icon_path = icon_path
        self.create_time = create_time
        self.update_time = update_time
        self.is_deleted = is_deleted

    def to_json(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "version": self.version,
        }