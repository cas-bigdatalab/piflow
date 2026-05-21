#!/usr/bin/env python3
"""PDF页面裁剪工具"""

import argparse
import os
import sys

from pypdf import PdfReader, PdfWriter


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
    parser = argparse.ArgumentParser(description='PDF页面裁剪工具')
    parser.add_argument('--input_path', required=True, help='输入PDF文件路径')
    parser.add_argument('--output_path', required=True, help='输出PDF文件路径')
    parser.add_argument('--bbox', required=True,
                        help='裁剪边界"left,bottom,right,top"（PDF坐标单位）')
    parser.add_argument('--pages', help='页码范围，如"1-3,5"（可选，默认全部）')
    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: file not found: {args.input_path}")
        sys.exit(1)

    try:
        left, bottom, right, top = map(float, args.bbox.split(','))
    except ValueError:
        print("Error: bbox must be in format 'left,bottom,right,top'")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output_path) or '.', exist_ok=True)

    reader = PdfReader(args.input_path)
    total = len(reader.pages)
    page_indices = _parse_pages(args.pages, total)

    writer = PdfWriter()
    for i in page_indices:
        page = reader.pages[i]
        page.mediabox.left = left
        page.mediabox.bottom = bottom
        page.mediabox.right = right
        page.mediabox.top = top
        writer.add_page(page)

    with open(args.output_path, 'wb') as f:
        writer.write(f)

    print(f"Cropped {len(page_indices)}/{total} pages to [{left}, {bottom}, {right}, {top}] -> {args.output_path}")


if __name__ == '__main__':
    main()
