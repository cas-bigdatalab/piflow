from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.s3_source_service import download_s3_source_file


def run(source_id: str, input_file_path: str, output_path: str) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    normalized_input_file_path = input_file_path.strip().lstrip("/")
    if not normalized_input_file_path:
        raise ValueError("input_file_path must not be empty")

    with tempfile.TemporaryDirectory(prefix="s3_source_", dir=str(output.parent)) as temp_dir:
        result = download_s3_source_file(
            source_id,
            relative_path=normalized_input_file_path,
            target_dir=temp_dir,
        )
        downloaded_path = Path(result["localPath"]).expanduser().resolve()
        if not downloaded_path.exists() or not downloaded_path.is_file():
            raise FileNotFoundError(f"downloaded s3 file not found: {downloaded_path}")
        shutil.copy2(downloaded_path, output)

    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download an S3 file by datasource instance id and input file path."
    )
    parser.add_argument("--source_id", required=True, help="S3 数据源实例 ID")
    parser.add_argument("--input_file_path", required=True, help="需要下载的 S3 对象相对路径，允许以 / 开头")
    parser.add_argument("--output", required=True, help="下载后的本地文件输出路径")
    args = parser.parse_args()

    output = run(
        source_id=args.source_id,
        input_file_path=args.input_file_path,
        output_path=args.output,
    )
    print(output)


if __name__ == "__main__":
    main()
