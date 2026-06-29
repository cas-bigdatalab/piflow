#!/usr/bin/env python3
"""PDF文本提取工具"""

import argparse
import os
import sys

from pypdf import PdfReader


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
    parser = argparse.ArgumentParser(description='PDF文本提取工具')
    parser.add_argument('--input_path', required=True, help='输入PDF文件路径')
    parser.add_argument('--output_path', required=True, help='输出txt文件路径')
    parser.add_argument('--pages', help='页码范围，如"1-3,5"（可选）')
    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: file not found: {args.input_path}")
        sys.exit(1)

    reader = PdfReader(args.input_path)
    total = len(reader.pages)
    page_indices = _parse_pages(args.pages, total)

    os.makedirs(os.path.dirname(args.output_path) or '.', exist_ok=True)

    with open(args.output_path, 'w', encoding='utf-8') as f:
        for i in page_indices:
            text = reader.pages[i].extract_text()
            f.write(f"--- Page {i+1} ---\n{text}\n\n")

    print(f"Extracted text from {len(page_indices)}/{total} pages -> {args.output_path}")


if __name__ == '__main__':
    main()
