from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.dataspace_source_service import download_dataspace_source_file


def run(datasource_id: str, relative_path: str, output_path: str) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="dataspace_source_", dir=str(output.parent)) as temp_dir:
        result = download_dataspace_source_file(
            datasource_id,
            relative_path=relative_path,
            target_dir=temp_dir,
        )
        downloaded_path = Path(result["localPath"]).expanduser().resolve()
        if not downloaded_path.exists() or not downloaded_path.is_file():
            raise FileNotFoundError(f"downloaded dataspace file not found: {downloaded_path}")
        shutil.copy2(downloaded_path, output)

    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a Dataspace file by datasource instance id and relative path."
    )
    parser.add_argument("--datasource_id", required=True, help="Dataspace 数据源实例 ID")
    parser.add_argument("--relative_path", required=True, help="Dataspace 空间内相对文件路径")
    parser.add_argument("--output", required=True, help="下载后的本地文件输出路径")
    args = parser.parse_args()

    output = run(
        datasource_id=args.datasource_id,
        relative_path=args.relative_path,
        output_path=args.output,
    )
    print(output)


if __name__ == "__main__":
    main()
