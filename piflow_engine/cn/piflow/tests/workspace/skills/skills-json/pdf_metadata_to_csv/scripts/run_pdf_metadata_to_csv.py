#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF元数据JSON转CSV工具")
    parser.add_argument("--metadata_path", required=True, help="输入元数据JSON路径")
    parser.add_argument("--output_path", required=True, help="输出CSV路径")
    args = parser.parse_args()

    if not os.path.exists(args.metadata_path):
        print(f"Error: metadata file not found: {args.metadata_path}")
        return 1

    with open(args.metadata_path, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    if not isinstance(metadata, dict):
        print("Error: metadata JSON must be an object")
        return 1

    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)
    fieldnames = list(metadata.keys())
    with open(args.output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({key: _stringify(value) for key, value in metadata.items()})

    print(f"Converted metadata JSON -> CSV: {args.output_path}")
    return 0


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
