"""Chemical PostgreSQL-backed service."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Callable, Iterable

from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

from database.postgres import get_connection

from .config import ChemicalConfig, ChemicalNode, load_chemical_config
from .node_repository import (
    change_running_count,
    ensure_software_instances,
    ensure_schema,
    fetch_node_record,
    fetch_node_records,
    has_software as db_has_software,
    set_running_count,
    sync_config_nodes,
    update_node_resource,
)


@dataclass(frozen=True)
class ChemicalSoftwareInstanceRow:
    node_name: str
    instances: dict[str, int]


@dataclass(frozen=True)
class ChemicalNodeDetail:
    name: str
    ip: str
    port: int
    software: tuple[str, ...]
    cpu_cores: float | None
    memory_gb: float | None
    free_disk_gb: float | None
    hostname: str
    status: str
    error_message: str
    last_refreshed_at: datetime | None
    software_instances: dict[str, int]


class ChemicalService:
    def __init__(
        self,
        config_path: str | Path,
        *,
        client_factory: Callable[[str], RemoteExecutionClient] = RemoteExecutionClient,
        max_workers: int = 8,
    ) -> None:
        self._config_path = Path(config_path)
        self._client_factory = client_factory
        self._max_workers = max(1, max_workers)
        self._lock = RLock()
        self._config = load_chemical_config(self._config_path)

    @property
    def config(self) -> ChemicalConfig:
        return self._config

    def initialize(self) -> None:
        with get_connection() as conn:
            ensure_schema(conn)
            self._sync_config(conn, self._config.nodes)

    def ensure_schema(self) -> None:
        with get_connection() as conn:
            ensure_schema(conn)

    def reload_config(self) -> ChemicalConfig:
        config = load_chemical_config(self._config_path)
        with self._lock:
            self._config = config
        return config

    def refresh(self) -> list[ChemicalNodeDetail]:
        with self._lock:
            config = self._config

        self.initialize()

        nodes = config.nodes
        if not nodes:
            return []

        rows: list[ChemicalNodeDetail] = []
        worker_count = min(self._max_workers, len(nodes))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {executor.submit(self._refresh_node, node): node for node in nodes}
            for future in as_completed(futures):
                node = futures[future]
                try:
                    detail = future.result()
                except Exception as exc:  # pragma: no cover - defensive fallback
                    detail = self._failed_detail(node, str(exc))
                rows.append(detail)

        rows.sort(key=lambda item: item.name)
        with get_connection() as conn:
            for row in rows:
                update_node_resource(
                    conn,
                    node_name=row.name,
                    cpu_cores=row.cpu_cores,
                    memory_gb=row.memory_gb,
                    free_disk_gb=row.free_disk_gb,
                    hostname=row.hostname,
                    status=row.status,
                    error_message=row.error_message,
                )
        return rows

    def list_node_details(self) -> list[ChemicalNodeDetail]:
        self.ensure_schema()
        with get_connection() as conn:
            records = fetch_node_records(conn)
        return [self._record_to_detail(record) for record in records]

    def get_node_detail(self, node_name: str) -> ChemicalNodeDetail:
        self.ensure_schema()
        with get_connection() as conn:
            record = fetch_node_record(conn, node_name)
        if record is None:
            raise KeyError(f"chemical node not found: {node_name}")
        return self._record_to_detail(record)

    def get_node(self, node_name: str) -> ChemicalNodeDetail:
        """Backward-compatible alias for database-backed node lookup."""

        return self.get_node_detail(node_name)

    def has_software(self, node_name: str, software: str) -> bool:
        self.ensure_schema()
        with get_connection() as conn:
            return db_has_software(conn, node_name=node_name, software=software)

    def change_software_instance_count(self, node_name: str, software: str, delta: int) -> None:
        self.ensure_schema()
        with get_connection() as conn:
            change_running_count(conn, node_name=node_name, software=software, delta=delta)

    def increment_software_instance_count(self, node_name: str, software: str, delta: int = 1) -> None:
        self.change_software_instance_count(node_name, software, delta)

    def set_software_instance_count(self, node_name: str, software: str, count: int) -> None:
        self.ensure_schema()
        with get_connection() as conn:
            set_running_count(conn, node_name=node_name, software=software, count=count)

    def list_software_columns(self) -> tuple[str, ...]:
        return tuple(sorted({software for node in self._config.nodes for software in node.software}))

    def list_software_instance_table(self) -> list[ChemicalSoftwareInstanceRow]:
        return [
            ChemicalSoftwareInstanceRow(
                node_name=detail.name,
                instances=dict(detail.software_instances),
            )
            for detail in self.list_node_details()
        ]

    def _sync_config(self, conn, nodes: Iterable[ChemicalNode]) -> None:
        node_rows = [
            {"name": node.name, "ip": node.ip, "port": node.port, "software": node.software}
            for node in nodes
        ]
        sync_config_nodes(conn, node_rows)
        ensure_software_instances(conn, node_rows)

    def _refresh_node(self, node: ChemicalNode) -> ChemicalNodeDetail:
        target = f"{node.ip}:{node.port}"
        client = self._client_factory(target)
        try:
            resource = client.get_server_resource()
            return ChemicalNodeDetail(
                name=node.name,
                ip=node.ip,
                port=node.port,
                software=node.software,
                cpu_cores=float(resource.cpu_cores),
                memory_gb=float(resource.memory_gb),
                free_disk_gb=float(resource.free_disk_gb),
                hostname=str(resource.hostname or ""),
                status="healthy",
                error_message="",
                last_refreshed_at=datetime.now().astimezone(),
                software_instances={},
            )
        except Exception as exc:
            return self._failed_detail(node, str(exc))
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    @staticmethod
    def _failed_detail(node: ChemicalNode, error_message: str) -> ChemicalNodeDetail:
        return ChemicalNodeDetail(
            name=node.name,
            ip=node.ip,
            port=node.port,
            software=node.software,
            cpu_cores=None,
            memory_gb=None,
            free_disk_gb=None,
            hostname="",
            status="unreachable",
            error_message=error_message,
            last_refreshed_at=datetime.now().astimezone(),
            software_instances={},
        )

    @staticmethod
    def _record_to_detail(record) -> ChemicalNodeDetail:
        software = tuple(str(item) for item in record.get("software") or [])
        software_instances = dict(record.get("software_instances") or {})
        return ChemicalNodeDetail(
            name=str(record["name"]),
            ip=str(record["ip"]),
            port=int(record["port"]),
            software=software,
            cpu_cores=record.get("cpu_cores"),
            memory_gb=record.get("memory_gb"),
            free_disk_gb=record.get("free_disk_gb"),
            hostname=str(record.get("hostname") or ""),
            status=str(record.get("status") or "unknown"),
            error_message=str(record.get("error_message") or ""),
            last_refreshed_at=record.get("last_refreshed_at"),
            software_instances={str(k): int(v) for k, v in software_instances.items()},
        )


class ChemicalNodeResourceService(ChemicalService):
    """Backward-compatible alias for the previous service name."""


ChemicalNodeResource = ChemicalNodeDetail
