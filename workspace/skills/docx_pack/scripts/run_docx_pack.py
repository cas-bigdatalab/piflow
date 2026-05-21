#!/usr/bin/env python3
"""DOCX打包工具 - 将解压的XML目录重新打包为DOCX文件"""

import argparse
import os
import sys
import zipfile
from pathlib import Path

import defusedxml.minidom


def _fix_durable_id(xml_path: Path) -> bool:
    """修复超过0x7FFFFFFF的durableId"""
    try:
        content = xml_path.read_text(encoding="utf-8")
        if "durableId" in content:
            dom = defusedxml.minidom.parseString(content)
            modified = False
            for elem in dom.getElementsByTagName("*"):
                if "durableId" in elem.attributes:
                    val = elem.getAttribute("durableId")
                    try:
                        if int(val, 16) >= 0x7FFFFFFF:
                            new_val = f"{0x7FFFFFFE:08X}"
                            elem.setAttribute("durableId", new_val)
                            modified = True
                    except ValueError:
                        pass
            if modified:
                xml_path.write_text(dom.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8"))
                return True
        return False
    except Exception:
        return False


def _fix_xml_space(content: str) -> str:
    """为包含空白的w:t元素添加xml:space="preserve"属性"""
    try:
        dom = defusedxml.minidom.parseString(content)
        modified = False
        for t_elem in dom.getElementsByTagName("w:t"):
            if t_elem.firstChild and t_elem.firstChild.nodeValue:
                text = t_elem.firstChild.nodeValue
                if text.startswith(" ") or text.endswith(" "):
                    if "xml:space" not in t_elem.attributes:
                        t_elem.setAttribute("xml:space", "preserve")
                        modified = True
        if modified:
            return dom.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
        return content
    except Exception:
        return content


def pack_docx(input_dir: str, output_path: str, original_path: str = None, 
              validate: bool = True) -> tuple[dict, str]:
    """
    将解压的XML目录打包为DOCX文件
    
    Args:
        input_dir: 解压的XML目录路径
        output_path: 输出DOCX文件路径
        original_path: 原始DOCX文件路径（用于参考）
        validate: 是否启用自动修复
    
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
    
    fixes_applied = []
    
    if validate:
        comments_ids = input_dir / "word" / "commentsIds.xml"
        if comments_ids.exists():
            if _fix_durable_id(comments_ids):
                fixes_applied.append("Fixed durableId in commentsIds.xml")
        
        comments_extensible = input_dir / "word" / "commentsExtensible.xml"
        if comments_extensible.exists():
            if _fix_durable_id(comments_extensible):
                fixes_applied.append("Fixed durableId in commentsExtensible.xml")
    
    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            for file_path in sorted(input_dir.rglob("*")):
                if file_path.is_file():
                    arcname = file_path.relative_to(input_dir)
                    content = file_path.read_bytes()
                    if file_path.suffix == ".xml":
                        try:
                            xml_str = content.decode("utf-8")
                            if validate:
                                xml_str = _fix_xml_space(xml_str)
                            content = xml_str.encode("utf-8")
                        except Exception:
                            pass
                    zip_ref.writestr(str(arcname), content)
    except Exception as e:
        return None, f"Error: Failed to create ZIP file: {e}"
    
    metadata = {
        "output_file": output_path.name,
        "file_size": output_path.stat().st_size,
        "files_packed": len([f for f in input_dir.rglob("*") if f.is_file()]),
        "fixes_applied": fixes_applied,
    }
    
    message = f"Successfully packed {input_dir} -> {output_path}"
    if fixes_applied:
        message += f"\n  Auto-repaired: {', '.join(fixes_applied)}"
    
    return metadata, message


def main():
    parser = argparse.ArgumentParser(description="将解压的XML目录打包为DOCX文件")
    parser.add_argument("--input_dir", required=True, help="解压的XML目录路径")
    parser.add_argument("--output_path", required=True, help="输出DOCX文件路径")
    parser.add_argument("--original", help="原始DOCX文件路径（可选）")
    parser.add_argument("--validate", action="store_true", default=True,
                        help="启用自动修复（默认开启）")
    args = parser.parse_args()
    
    metadata, message = pack_docx(args.input_dir, args.output_path, args.original, args.validate)
    
    print(message)
    if "Error" in message:
        sys.exit(1)


if __name__ == "__main__":
    main()
