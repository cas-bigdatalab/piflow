#!/usr/bin/env python3
"""PDF页面旋转工具"""

import argparse
import os
import sys

from pypdf import PdfReader, PdfWriter


def _parse_pages(spec, total):
    if not spec:
        return None
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
    parser = argparse.ArgumentParser(description='PDF页面旋转工具')
    parser.add_argument('--input_path', required=True, help='输入PDF文件路径')
    parser.add_argument('--output_path', required=True, help='输出PDF文件路径')
    parser.add_argument('--angle', type=int, default=90,
                        choices=[90, 180, 270], help='旋转角度（90/180/270）')
    parser.add_argument('--pages', help='页码范围，如"1-3,5"（可选，默认全部）')
    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: file not found: {args.input_path}")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output_path) or '.', exist_ok=True)

    reader = PdfReader(args.input_path)
    total = len(reader.pages)
    target_pages = _parse_pages(args.pages, total)

    writer = PdfWriter()
    for i in range(total):
        page = reader.pages[i]
        if target_pages is None or i in target_pages:
            page.rotate(args.angle)
        writer.add_page(page)

    with open(args.output_path, 'wb') as f:
        writer.write(f)

    rotated = target_pages or list(range(total))
    print(f"Rotated {len(rotated)}/{total} pages by {args.angle} degrees -> {args.output_path}")


if __name__ == '__main__':
    main()
