"""Local file integrity and containment; no download or cloud cache policy."""
from hashlib import sha256
from pathlib import Path, PurePosixPath


def safe_path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if parts.is_absolute() or ".." in parts.parts or "\\" in relative or ":" in relative:
        raise ValueError("资源路径必须是目录内的相对路径")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("资源路径超出配置目录")
    return path


def file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path, expected: dict):
    if not path.is_file():
        raise FileNotFoundError(f"缺少数据文件：{path}；请检查sources.yaml中的目录")
    if path.stat().st_size != expected["size"] or file_hash(path) != expected["sha256"]:
        raise ValueError(f"数据校验失败：{path}；请使用完整的同版本数据包")
