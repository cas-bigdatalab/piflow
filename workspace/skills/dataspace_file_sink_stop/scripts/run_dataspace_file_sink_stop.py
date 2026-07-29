from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.dataspace_source_service import upload_dataspace_source_directory


def str_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def run(
    input_path: str,
    datasource_id: str,
    relative_path: str,
    overwrite: bool,
    output_path: str,
) -> Path:
    source_path = Path(input_path).expanduser().resolve()
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"dataspace file sink input file not found: {source_path}")

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    managed_dir = output.parent / "_dataspace_sink_managed"
    staged_path = managed_dir / Path(relative_path.strip().lstrip("/"))
    if staged_path.exists() and not overwrite:
        raise FileExistsError(f"managed sink path already exists: {staged_path}")

    staged_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, staged_path)

    upload_dataspace_source_directory(
        datasource_id,
        remote_relative_path=".",
        local_dir=managed_dir,
    )

    shutil.copy2(staged_path, output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload a managed local file into a Dataspace directory by datasource instance id."
    )
    parser.add_argument("--input", required=True, help="上游算子的文件输出引用")
    parser.add_argument("--datasource_id", required=True, help="Dataspace 数据源实例 ID")
    parser.add_argument("--relative_path", required=True, help="上传到 Dataspace 时使用的空间内相对文件路径")
    parser.add_argument("--overwrite", default="false", help="本地托管目录中存在同名文件时是否允许覆盖")
    parser.add_argument("--output", required=True, help="上传后保留的本地文件输出路径")
    args = parser.parse_args()

    output = run(
        input_path=args.input,
        datasource_id=args.datasource_id,
        relative_path=args.relative_path,
        overwrite=str_to_bool(args.overwrite),
        output_path=args.output,
    )
    print(output)


if __name__ == "__main__":
    main()
