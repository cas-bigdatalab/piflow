#!/usr/bin/env python3
"""XLSX打包工具 - 将解压的XML目录重新打包为XLSX文件"""

import argparse
import os
import sys
import zipfile
from pathlib import Path


def pack_xlsx(input_dir: str, output_path: str) -> tuple[dict, str]:
    """
    将解压的XML目录打包为XLSX文件
    
    Args:
        input_dir: 解压的XML目录路径
        output_path: 输出XLSX文件路径
    
    Returns:
        (metadata, message)
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)
    
    if not input_dir.exists():
        return None, f"Error: Input directory not found: {input_dir}"
    
    if not input_dir.is_dir():
        return None, f"Error: Input path is not a directory: {input_dir}"
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return None, f"Error: Failed to create output directory: {e}"
    
    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            for file_path in sorted(input_dir.rglob("*")):
                if file_path.is_file():
                    arcname = file_path.relative_to(input_dir)
                    content = file_path.read_bytes()
                    zip_ref.writestr(str(arcname), content)
    except Exception as e:
        return None, f"Error: Failed to create ZIP file: {e}"
    
    metadata = {
        "output_file": output_path.name,
        "file_size": output_path.stat().st_size,
        "files_packed": len([f for f in input_dir.rglob("*") if f.is_file()]),
    }
    
    return metadata, f"Successfully packed {input_dir} -> {output_path}"


def main():
    parser = argparse.ArgumentParser(description="将解压的XML目录打包为XLSX文件")
    parser.add_argument("--input_dir", required=True, help="解压的XML目录路径")
    parser.add_argument("--output_path", required=True, help="输出XLSX文件路径")
    args = parser.parse_args()
    
    metadata, message = pack_xlsx(args.input_dir, args.output_path)
    
    print(message)
    if "Error" in message:
        sys.exit(1)


if __name__ == "__main__":
    main()
