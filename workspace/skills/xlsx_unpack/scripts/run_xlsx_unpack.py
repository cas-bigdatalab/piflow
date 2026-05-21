#!/usr/bin/env python3
"""XLSX解压工具 - 将XLSX文件解压为XML目录"""

import argparse
import os
import sys
import zipfile
from pathlib import Path


def unpack_xlsx(input_path: str, output_dir: str) -> tuple[dict, str]:
    """
    解压XLSX文件到指定目录
    
    Args:
        input_path: 输入XLSX文件路径
        output_dir: 输出目录路径
    
    Returns:
        (metadata, message)
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        return None, f"Error: Input file not found: {input_path}"
    
    if input_path.suffix.lower() not in (".xlsx", ".xlsm"):
        return None, f"Error: Input file is not an XLSX/XLSM file: {input_path}"
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return None, f"Error: Failed to create output directory: {e}"
    
    try:
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            namelist = zip_ref.namelist()
            for name in namelist:
                if name.endswith("/"):
                    continue
                output_path = output_dir / name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                content = zip_ref.read(name)
                if name.endswith(".xml"):
                    try:
                        xml_str = content.decode("utf-8")
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(xml_str)
                    except Exception:
                        with open(output_path, "wb") as f:
                            f.write(content)
                else:
                    with open(output_path, "wb") as f:
                        f.write(content)
    except zipfile.BadZipFile:
        return None, f"Error: Invalid ZIP file (not a valid XLSX)"
    except Exception as e:
        return None, f"Error: Failed to extract files: {e}"
    
    metadata = {
        "file_name": input_path.name,
        "file_size": input_path.stat().st_size,
        "extracted_files": len([f for f in output_dir.rglob("*") if f.is_file()]),
    }
    
    return metadata, f"Successfully unpacked {input_path.name} -> {output_dir}"


def main():
    parser = argparse.ArgumentParser(description="将XLSX文件解压为XML目录")
    parser.add_argument("--input_path", required=True, help="输入XLSX文件路径")
    parser.add_argument("--output_dir", required=True, help="输出目录路径")
    args = parser.parse_args()
    
    metadata, message = unpack_xlsx(args.input_path, args.output_dir)
    
    print(message)
    if "Error" in message:
        sys.exit(1)


if __name__ == "__main__":
    main()
