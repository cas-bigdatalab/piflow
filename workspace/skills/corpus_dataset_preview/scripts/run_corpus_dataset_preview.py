import argparse
import json
import os
import sys
from typing import Any

import requests


BASE_URL = "http://172.31.3.81:7005"
ENDPOINT = f"{BASE_URL}/corpus.dataset.preview"


def write_json(path: str, payload: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Corpus dataset preview proxy")
    parser.add_argument("--cstr", required=True)
    parser.add_argument("--output", default="corpus_dataset_preview_output.json")
    args = parser.parse_args()
    cstr = args.cstr.strip()
    if not cstr:
        parser.error("cstr must not be empty")

    try:
        response = requests.get(ENDPOINT, params={"cstr": cstr}, headers={"accept": "*/*"}, timeout=60)
        response.raise_for_status()
        body = response.json()
        result = {"success": True, "skill": "corpus_dataset_preview", "request": {"cstr": cstr}, "response": body}
        write_json(args.output, result)
        print(f"[OK] corpus_dataset_preview completed; output: {args.output}")
        return 0
    except (requests.RequestException, ValueError) as exc:
        error = {"success": False, "skill": "corpus_dataset_preview", "request": {"cstr": cstr}, "error": str(exc)}
        write_json(args.output, error)
        print(f"[ERROR] corpus_dataset_preview failed; output: {args.output}; error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
