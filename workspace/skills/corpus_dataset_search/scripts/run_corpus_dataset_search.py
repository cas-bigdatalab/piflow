import argparse
import json
import os
import sys
from typing import Any

import requests


BASE_URL = "http://172.31.3.81:7005"
ENDPOINT = f"{BASE_URL}/dataset.page"


def write_json(path: str, payload: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="数据集分页检索接口代理")
    parser.add_argument("--page_num", type=int, default=1)
    parser.add_argument("--page_size", type=int, default=10)
    parser.add_argument("--title")
    parser.add_argument("--field")
    parser.add_argument("--subject")
    parser.add_argument("--author")
    parser.add_argument("--doi")
    parser.add_argument("--output", default="corpus_dataset_search_output.json")
    args = parser.parse_args()

    if args.page_num < 1 or args.page_size < 1:
        parser.error("page_num and page_size must be positive")

    filters = {
        key: value
        for key, value in {
            "title": args.title,
            "field": args.field,
            "subject": args.subject,
            "author": args.author,
            "doi": args.doi,
        }.items()
        if value not in (None, "")
    }
    request_info = {"page_num": args.page_num, "page_size": args.page_size, **filters}
    try:
        response = requests.post(
            ENDPOINT,
            params={"pageNum": args.page_num, "pageSize": args.page_size},
            json=filters,
            headers={"accept": "*/*", "Content-Type": "application/json"},
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        result = {"success": True, "skill": "corpus_dataset_search", "request": request_info, "response": body}
        write_json(args.output, result)
        print(f"[OK] corpus_dataset_search completed; output: {args.output}")
        return 0
    except (requests.RequestException, ValueError) as exc:
        error = {"success": False, "skill": "corpus_dataset_search", "request": request_info, "error": str(exc)}
        write_json(args.output, error)
        print(f"[ERROR] corpus_dataset_search failed; output: {args.output}; error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
