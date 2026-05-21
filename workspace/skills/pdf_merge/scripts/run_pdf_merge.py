#!/usr/bin/env python3
"""PDF合并工具"""

import argparse
import os
import sys

from pypdf import PdfReader, PdfWriter


def main():
    parser = argparse.ArgumentParser(description='PDF合并工具')
    parser.add_argument('--input_paths', nargs='+', required=True,
                        help='输入PDF文件路径（多个以空格分隔）')
    parser.add_argument('--output_path', required=True, help='输出PDF文件路径')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_path) or '.', exist_ok=True)

    writer = PdfWriter()
    total_pages = 0
    for path in args.input_paths:
        if not os.path.exists(path):
            print(f"Warning: file not found, skipping: {path}")
            continue
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
        total_pages += len(reader.pages)
        print(f"  Added {len(reader.pages)} pages from {os.path.basename(path)}")

    with open(args.output_path, 'wb') as f:
        writer.write(f)

    print(f"Merged {len(args.input_paths)} files ({total_pages} pages) -> {args.output_path}")


if __name__ == '__main__':
    main()
