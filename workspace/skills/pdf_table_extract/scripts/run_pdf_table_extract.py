#!/usr/bin/env python3
"""PDF表格提取工具"""

import argparse
import json
import os
import sys

import pdfplumber


def _parse_pages(spec, total):
    if not spec:
        return list(range(total))
    indices = set()
    for part in spec.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            start = int(start.strip()) - 1
            end = int(end.strip()) - 1
            indices.update(range(max(0, start), min(total, end + 1)))
        else:
            idx = int(part) - 1
            if 0 <= idx < total:
                indices.add(idx)
    return sorted(indices)


def main():
    parser = argparse.ArgumentParser(description='PDF表格提取工具')
    parser.add_argument('--input_path', required=True, help='输入PDF文件路径')
    parser.add_argument('--output_path', required=True, help='输出JSON文件路径')
    parser.add_argument('--pages', help='页码范围，如"1-3,5"（可选）')
    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: file not found: {args.input_path}")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output_path) or '.', exist_ok=True)

    result = []
    with pdfplumber.open(args.input_path) as pdf:
        total = len(pdf.pages)
        page_indices = _parse_pages(args.pages, total)
        for i in page_indices:
            page = pdf.pages[i]
            tables = page.extract_tables()
            for t in tables:
                if t and len(t) > 1:
                    row_data = [dict(zip(t[0], row)) for row in t[1:] if row]
                    result.append({
                        "page": i + 1,
                        "headers": t[0],
                        "rows": row_data
                    })

    with open(args.output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    table_count = len(result)
    row_count = sum(len(t['rows']) for t in result)
    print(f"Extracted {table_count} tables ({row_count} rows) from {len(page_indices)} pages -> {args.output_path}")


if __name__ == '__main__':
    main()
