#!/usr/bin/env python3
"""PDF拆分工具"""

import argparse
import os
import sys

from pypdf import PdfReader, PdfWriter


def _parse_pages(spec, total):
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
    parser = argparse.ArgumentParser(description='PDF拆分工具')
    parser.add_argument('--input_path', required=True, help='输入PDF文件路径')
    parser.add_argument('--output_path', required=True, help='输出PDF文件路径')
    parser.add_argument('--pages', help='页码范围，如"1-3,5"（可选，默认全部拆为单页）')
    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: file not found: {args.input_path}")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output_path) or '.', exist_ok=True)

    reader = PdfReader(args.input_path)
    total = len(reader.pages)
    page_indices = _parse_pages(args.pages, total) if args.pages else list(range(total))
    base, ext = os.path.splitext(args.output_path)

    if len(page_indices) == 1:
        writer = PdfWriter()
        writer.add_page(reader.pages[page_indices[0]])
        with open(args.output_path, 'wb') as f:
            writer.write(f)
        print(f"Extracted page {page_indices[0]+1} -> {args.output_path}")
    else:
        for idx, i in enumerate(page_indices):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            out = f"{base}_page{i+1}{ext}"
            with open(out, 'wb') as f:
                writer.write(f)
            print(f"  Page {i+1} -> {os.path.basename(out)}")
        print(f"Split {len(page_indices)} pages from {os.path.basename(args.input_path)}")


if __name__ == '__main__':
    main()
