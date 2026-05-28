#!/usr/bin/env python3
"""PDF元数据提取工具"""

import argparse
import json
import os
import sys

from pypdf import PdfReader


def main():
    parser = argparse.ArgumentParser(description='PDF元数据提取工具')
    parser.add_argument('--input_path', required=True, help='输入PDF文件路径')
    parser.add_argument('--output_path', required=True, help='输出JSON文件路径')
    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: file not found: {args.input_path}")
        sys.exit(1)

    reader = PdfReader(args.input_path)
    meta = reader.metadata

    info = {
        "file_name": os.path.basename(args.input_path),
        "file_size": os.path.getsize(args.input_path),
        "pages": len(reader.pages),
        "pdf_version": reader.pdf_header if hasattr(reader, 'pdf_header') else None,
        "title": meta.title,
        "author": meta.author,
        "subject": meta.subject,
        "creator": meta.creator,
        "producer": meta.producer,
        "creation_date": str(meta.creation_date) if meta.creation_date else None,
        "modification_date": str(meta.modification_date) if meta.modification_date else None,
        "is_encrypted": reader.is_encrypted,
    }

    os.makedirs(os.path.dirname(args.output_path) or '.', exist_ok=True)
    with open(args.output_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print(f"Extracted metadata -> {args.output_path}")
    print(f"  Pages: {info['pages']}")
    print(f"  Title: {info['title'] or 'N/A'}")
    print(f"  Author: {info['author'] or 'N/A'}")


if __name__ == '__main__':
    main()
