from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from piflow_engine.cn.piflow.engine.datasource.dataspace_client import DataspaceClient


@dataclass(frozen=True)
class DataspaceSource:
    source_id: str
    name: str
    base_url: str
    app_id: str
    auth_code: str
    space_name: str
    space_id: str
    ftp_user: str
    ftp_password: str
    ftp_link: str
    webdav_link: str
    root_path: str
    logo: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_client(self) -> DataspaceClient:
        return DataspaceClient(
            base_url=self.base_url,
            app_id=self.app_id,
            auth_code=self.auth_code,
        )
