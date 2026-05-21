#!/usr/bin/env python3
"""DOCX文本提取工具 - 从DOCX文件中提取文本内容"""

import argparse
import os
import sys
import zipfile
from pathlib import Path

import defusedxml.minidom


def extract_text_from_docx(input_path: str) -> tuple[str, str]:
    """
    从DOCX文件中提取文本内容
    
    Args:
        input_path: 输入DOCX文件路径
    
    Returns:
        (text, message)
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        return "", f"Error: Input file not found: {input_path}"
    
    if not input_path.suffix.lower() == ".docx":
        return "", f"Error: Input file is not a DOCX file: {input_path}"
    
    try:
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            if "word/document.xml" not in zip_ref.namelist():
                return "", "Error: document.xml not found in DOCX"
            
            content = zip_ref.read("word/document.xml")
            xml_str = content.decode("utf-8")
            
            dom = defusedxml.minidom.parseString(xml_str)
            text_parts = []
            
            for t_elem in dom.getElementsByTagName("w:t"):
                if t_elem.firstChild and t_elem.firstChild.nodeValue:
                    text_parts.append(t_elem.firstChild.nodeValue)
            
            text = "\n".join(text_parts)
            
            if not text.strip():
                return "", "Warning: No text found in document"
            
            return text, f"Successfully extracted {len(text)} characters"
    
    except zipfile.BadZipFile:
        return "", "Error: Invalid ZIP file (not a valid DOCX)"
    except Exception as e:
        return "", f"Error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="从DOCX文件中提取文本内容")
    parser.add_argument("--input_path", required=True, help="输入DOCX文件路径")
    parser.add_argument("--output_path", required=True, help="输出TXT文件路径")
    args = parser.parse_args()
    
    text, message = extract_text_from_docx(args.input_path)
    
    if "Error" in message:
        print(message)
        sys.exit(1)
    
    try:
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print(f"Error: Failed to write output file: {e}")
        sys.exit(1)
    
    print(message)


if __name__ == "__main__":
    main()
