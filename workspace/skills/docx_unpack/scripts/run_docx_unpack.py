#!/usr/bin/env python3
"""DOCX解压工具 - 将DOCX文件解压为XML目录"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path

import defusedxml.minidom


def _merge_runs(xml_content: str) -> str:
    """合并相邻的相同格式的文本运行"""
    try:
        dom = defusedxml.minidom.parseString(xml_content)
        for body in dom.getElementsByTagName("w:body"):
            for child in list(body.childNodes):
                if child.nodeType != child.ELEMENT_NODE:
                    continue
                if child.tagName != "w:p":
                    continue
                runs = []
                for node in list(child.childNodes):
                    if node.nodeType == node.ELEMENT_NODE and node.tagName == "w:r":
                        runs.append(node)
                if len(runs) < 2:
                    continue
                merged = []
                i = 0
                while i < len(runs):
                    current = runs[i]
                    next_i = i + 1
                    while next_i < len(runs):
                        next_run = runs[next_i]
                        if _runs_compatible(current, next_run):
                            _merge_into(current, next_run)
                            next_i += 1
                        else:
                            break
                    merged.append(current)
                    i = next_i
            for p in list(body.childNodes):
                if p.nodeType != p.ELEMENT_NODE or p.tagName != "w:p":
                    continue
                for node in list(p.childNodes):
                    if node.nodeType == node.ELEMENT_NODE and node.tagName == "w:r":
                        if node not in merged:
                            p.removeChild(node)
        return dom.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    except Exception:
        return xml_content


def _runs_compatible(run1, run2) -> bool:
    """检查两个运行是否可以合并（相同的格式属性）"""
    try:
        rpr1 = run1.getElementsByTagName("w:rPr")
        rpr2 = run2.getElementsByTagName("w:rPr")
        if len(rpr1) != len(rpr2):
            return False
        if len(rpr1) == 0:
            return True
        return rpr1[0].toxml() == rpr2[0].toxml()
    except Exception:
        return False


def _merge_into(target, source):
    """将source的文本内容合并到target"""
    try:
        t_text = target.getElementsByTagName("w:t")
        s_text = source.getElementsByTagName("w:t")
        if t_text and s_text:
            t_text[0].firstChild.nodeValue += s_text[0].firstChild.nodeValue
    except Exception:
        pass


def _encode_smart_quotes(text: str) -> str:
    """将智能引号转换为XML实体"""
    smart_quotes = {
        "\u201c": "&#x201C;",
        "\u201d": "&#x201D;",
        "\u2018": "&#x2018;",
        "\u2019": "&#x2019;",
    }
    for char, entity in smart_quotes.items():
        text = text.replace(char, entity)
    return text


def unpack_docx(input_path: str, output_dir: str, merge_runs: bool = True) -> tuple[dict, str]:
    """
    解压DOCX文件到指定目录
    
    Args:
        input_path: 输入DOCX文件路径
        output_dir: 输出目录路径
        merge_runs: 是否合并相邻的文本运行
    
    Returns:
        (metadata, message)
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        return None, f"Error: Input file not found: {input_path}"
    
    if not input_path.suffix.lower() == ".docx":
        return None, f"Error: Input file is not a DOCX file: {input_path}"
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return None, f"Error: Failed to create output directory: {e}"
    
    try:
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            namelist = zip_ref.namelist()
            for name in namelist:
                output_path = output_dir / name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                content = zip_ref.read(name)
                if name.endswith(".xml"):
                    try:
                        xml_str = content.decode("utf-8")
                        if merge_runs and "document.xml" in name:
                            xml_str = _merge_runs(xml_str)
                        xml_str = _encode_smart_quotes(xml_str)
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(xml_str)
                    except Exception:
                        with open(output_path, "wb") as f:
                            f.write(content)
                else:
                    with open(output_path, "wb") as f:
                        f.write(content)
    except zipfile.BadZipFile:
        return None, f"Error: Invalid ZIP file (not a valid DOCX)"
    except Exception as e:
        return None, f"Error: Failed to extract files: {e}"
    
    metadata = {
        "file_name": input_path.name,
        "file_size": input_path.stat().st_size,
        "extracted_files": len([f for f in output_dir.rglob("*") if f.is_file()]),
        "merge_runs": merge_runs,
    }
    
    return metadata, f"Successfully unpacked {input_path.name} -> {output_dir}"


def main():
    parser = argparse.ArgumentParser(description="将DOCX文件解压为XML目录")
    parser.add_argument("--input_path", required=True, help="输入DOCX文件路径")
    parser.add_argument("--output_dir", required=True, help="输出目录路径")
    parser.add_argument("--merge_runs", action="store_true", default=True,
                        help="合并相邻的文本运行（默认开启）")
    args = parser.parse_args()
    
    metadata, message = unpack_docx(args.input_path, args.output_dir, args.merge_runs)
    
    print(message)
    if "Error" in message:
        sys.exit(1)


if __name__ == "__main__":
    main()
