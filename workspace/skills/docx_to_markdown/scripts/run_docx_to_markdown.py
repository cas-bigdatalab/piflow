#!/usr/bin/env python3
"""DOCX转Markdown工具 - 将DOCX文档转换为Markdown格式"""

import argparse
import os
import sys
import zipfile
from pathlib import Path

import defusedxml.minidom


def parse_docx(input_path: str) -> str:
    """
    解析DOCX文件并转换为Markdown格式
    
    Args:
        input_path: 输入DOCX文件路径
    
    Returns:
        Markdown格式的文本
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        return f"Error: Input file not found: {input_path}"
    
    if not input_path.suffix.lower() == ".docx":
        return f"Error: Input file is not a DOCX file: {input_path}"
    
    try:
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            if "word/document.xml" not in zip_ref.namelist():
                return "Error: document.xml not found in DOCX"
            
            content = zip_ref.read("word/document.xml")
            xml_str = content.decode("utf-8")
            
            dom = defusedxml.minidom.parseString(xml_str)
            body = dom.getElementsByTagName("w:body")[0]
            
            markdown_parts = []
            list_level = 0
            in_table = False
            
            for child in body.childNodes:
                if child.nodeType != child.ELEMENT_NODE:
                    continue
                
                if child.tagName == "w:p":
                    paragraph = parse_paragraph(child)
                    if paragraph:
                        markdown_parts.append(paragraph)
                    list_level = 0
                    in_table = False
                
                elif child.tagName == "w:tbl":
                    table = parse_table(child)
                    if table:
                        markdown_parts.append(table)
                    in_table = True
            
            return "\n\n".join(markdown_parts)
    
    except zipfile.BadZipFile:
        return "Error: Invalid ZIP file (not a valid DOCX)"
    except Exception as e:
        return f"Error: {str(e)}"


def parse_paragraph(p_elem) -> str:
    """解析段落元素"""
    text_parts = []
    style = get_paragraph_style(p_elem)
    
    for child in p_elem.childNodes:
        if child.nodeType != child.ELEMENT_NODE:
            continue
        
        if child.tagName == "w:r":
            text = parse_run(child)
            if text:
                text_parts.append(text)
    
    text = "".join(text_parts).strip()
    if not text:
        return ""
    
    if style == "heading1":
        return f"# {text}"
    elif style == "heading2":
        return f"## {text}"
    elif style == "heading3":
        return f"### {text}"
    elif style == "heading4":
        return f"#### {text}"
    elif style == "heading5":
        return f"##### {text}"
    elif style == "heading6":
        return f"###### {text}"
    elif style == "listParagraph":
        return f"- {text}"
    elif style == "quote":
        return f"> {text}"
    else:
        return text


def get_paragraph_style(p_elem) -> str:
    """获取段落样式"""
    p_style = p_elem.getElementsByTagName("w:pStyle")
    if p_style:
        style_val = p_style[0].getAttribute("w:val")
        if style_val.startswith("Heading"):
            level = style_val.replace("Heading", "")
            return f"heading{level}"
        elif style_val == "ListParagraph":
            return "listParagraph"
        elif style_val == "Quote":
            return "quote"
    return "normal"


def parse_run(r_elem) -> str:
    """解析文本运行元素"""
    text = ""
    bold = False
    italic = False
    
    for child in r_elem.childNodes:
        if child.nodeType != child.ELEMENT_NODE:
            continue
        
        if child.tagName == "w:t":
            if child.firstChild and child.firstChild.nodeValue:
                text += child.firstChild.nodeValue
        
        elif child.tagName == "w:rPr":
            for prop in child.childNodes:
                if prop.nodeType == prop.ELEMENT_NODE:
                    if prop.tagName == "w:b":
                        bold = True
                    elif prop.tagName == "w:i":
                        italic = True
    
    if bold and italic:
        return f"**_{text}_**"
    elif bold:
        return f"**{text}**"
    elif italic:
        return f"_{text}_"
    return text


def parse_table(tbl_elem) -> str:
    """解析表格元素"""
    rows = []
    header = []
    
    for child in tbl_elem.childNodes:
        if child.nodeType != child.ELEMENT_NODE:
            continue
        
        if child.tagName == "w:tr":
            row_cells = []
            for tc_elem in child.getElementsByTagName("w:tc"):
                cell_text = ""
                for p_elem in tc_elem.getElementsByTagName("w:p"):
                    for r_elem in p_elem.getElementsByTagName("w:r"):
                        for t_elem in r_elem.getElementsByTagName("w:t"):
                            if t_elem.firstChild and t_elem.firstChild.nodeValue:
                                cell_text += t_elem.firstChild.nodeValue
                row_cells.append(cell_text.strip())
            
            if not header:
                header = row_cells
            else:
                rows.append(row_cells)
    
    if not header:
        return ""
    
    markdown = []
    markdown.append("| " + " | ".join(header) + " |")
    markdown.append("| " + " | ".join(["---"] * len(header)) + " |")
    
    for row in rows:
        markdown.append("| " + " | ".join(row) + " |")
    
    return "\n".join(markdown)


def main():
    parser = argparse.ArgumentParser(description="将DOCX文档转换为Markdown格式")
    parser.add_argument("--input_path", required=True, help="输入DOCX文件路径")
    parser.add_argument("--output_path", required=True, help="输出Markdown文件路径")
    args = parser.parse_args()
    
    markdown_text = parse_docx(args.input_path)
    
    if markdown_text.startswith("Error:"):
        print(markdown_text)
        sys.exit(1)
    
    try:
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
    except Exception as e:
        print(f"Error: Failed to write output file: {e}")
        sys.exit(1)
    
    print(f"Successfully converted {args.input_path} -> {args.output_path}")


if __name__ == "__main__":
    main()
