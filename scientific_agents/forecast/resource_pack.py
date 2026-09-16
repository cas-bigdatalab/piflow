"""Create an immutable manifest for explicitly selected, legally acquired CSV files."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from .files import safe_path


def pack(directory: Path, resource_id: str, version: str, files: list[str]) -> Path:
    if not resource_id.strip() or not version.strip() or not files or len(set(files)) != len(files):
        raise ValueError("资源编号、版本和不重复的文件列表不能为空")
    entries = {}
    for name in sorted(files):
        path = safe_path(directory, name)
        if path.suffix.lower() != ".csv" or not path.is_file():
            raise ValueError(f"请选择已准备好的CSV文件：{name}")
        digest = sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        entries[name] = {"size": path.stat().st_size, "sha256": digest.hexdigest()}
    data = {"resource_id": resource_id, "version": version, "files": entries}
    target = directory / "manifest.json"
    if target.exists():
        if json.loads(target.read_text(encoding="utf-8")) != data:
            raise ValueError("已有清单与输入不一致，请在新版本目录重新打包，不能覆盖旧版本")
    else:
        with target.open("x", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
    return target.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--file", required=True, action="append")
    args = parser.parse_args()
    print(pack(args.directory, args.resource_id, args.version, args.file))


if __name__ == "__main__":
    main()
