from __future__ import annotations

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class PostgresConfig:
    host: str = "10.0.87.112"
    port: int = 5432
    database: str = "mydb"
    user: str = "admin"
    password: str = "123456"
    sslmode: str = "prefer"

    @classmethod
    def from_env(cls, prefix: str = "PIFLOW_POSTGRES_") -> "PostgresConfig":
        return cls(
            host=os.getenv(f"{prefix}HOST", cls.host),
            port=int(os.getenv(f"{prefix}PORT", "5432")),
            database=os.getenv(f"{prefix}DATABASE", os.getenv(f"{prefix}DB", cls.database)),
            user=os.getenv(f"{prefix}USER", cls.user),
            password=os.getenv(f"{prefix}PASSWORD", cls.password),
            sslmode=os.getenv(f"{prefix}SSLMODE", cls.sslmode),
        )

    def dsn(self) -> str:
        parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.database}",
            f"user={self.user}",
            f"sslmode={self.sslmode}",
        ]
        if self.password:
            parts.append(f"password={self.password}")
        return " ".join(parts)

    def connect(self):
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError(
                "psycopg is installed but no PostgreSQL libpq wrapper is available; "
                "install psycopg[binary], psycopg-c, or system libpq"
            ) from error

        return psycopg.connect(self.dsn())
