from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--prefix", default="")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = input_path.read_text(encoding="utf-8")
    output_path.write_text(f"{args.prefix}{text}", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
