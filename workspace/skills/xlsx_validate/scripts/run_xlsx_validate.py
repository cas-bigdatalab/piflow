#!/usr/bin/env python3
"""XLSX验证工具 - 验证XLSX文件格式有效性"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path


def validate_xlsx(input_path: str) -> tuple[dict, str]:
    """
    验证XLSX文件格式有效性
    
    Args:
        input_path: 输入XLSX文件路径
    
    Returns:
        (result, message)
    """
    input_path = Path(input_path)
    
    result = {
        "valid": True,
        "file_exists": False,
        "is_zip": False,
        "has_required_files": False,
        "required_files": [],
        "missing_files": [],
        "file_size": 0,
        "total_files": 0,
        "errors": [],
        "warnings": [],
    }
    
    if not input_path.exists():
        result["valid"] = False
        result["errors"].append("File not found")
        return result, "Error: File not found"
    
    result["file_exists"] = True
    result["file_size"] = input_path.stat().st_size
    
    if input_path.suffix.lower() not in (".xlsx", ".xlsm"):
        result["warnings"].append("File extension is not .xlsx or .xlsm")
    
    try:
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            result["is_zip"] = True
            namelist = zip_ref.namelist()
            result["total_files"] = len(namelist)
            
            required_files = [
                "[Content_Types].xml",
                "_rels/.rels",
                "xl/workbook.xml",
                "xl/worksheets/sheet1.xml",
            ]
            
            result["required_files"] = required_files
            missing = []
            
            for req in required_files:
                if req not in namelist:
                    missing.append(req)
            
            if missing:
                result["missing_files"] = missing
                result["valid"] = False
                result["errors"].append(f"Missing required files: {', '.join(missing)}")
            else:
                result["has_required_files"] = True
    
    except zipfile.BadZipFile:
        result["valid"] = False
        result["errors"].append("Not a valid ZIP file")
        return result, "Error: Not a valid ZIP file"
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Unexpected error: {str(e)}")
        return result, f"Error: {str(e)}"
    
    if result["valid"]:
        return result, "XLSX file is valid"
    else:
        return result, f"XLSX validation failed: {', '.join(result['errors'])}"


def main():
    parser = argparse.ArgumentParser(description="验证XLSX文件格式有效性")
    parser.add_argument("--input_path", required=True, help="输入XLSX文件路径")
    parser.add_argument("--output_path", required=True, help="输出JSON结果文件路径")
    args = parser.parse_args()
    
    result, message = validate_xlsx(args.input_path)
    
    try:
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error: Failed to write output file: {e}")
        sys.exit(1)
    
    print(message)
    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
