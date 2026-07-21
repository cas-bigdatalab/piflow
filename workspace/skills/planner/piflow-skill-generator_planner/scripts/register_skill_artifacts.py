#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from generate_piflow_skill import read_spec_input, resolve_source_path, register_skill_artifacts


def main():
    parser = argparse.ArgumentParser(
        description="Register PiFlow skill metadata only, including docs/skill分类.txt and storage/skills icons."
    )
    parser.add_argument("--spec", help="UTF-8 JSON spec path")
    parser.add_argument("--flow", help="UTF-8 JSON successful workflow summary path")
    parser.add_argument("--restored-spec-out", help="Optional path to write restored spec when using --flow")
    parser.add_argument("--skill-dir", required=True, help="Existing generated skill directory path")
    args = parser.parse_args()

    spec = read_spec_input(
        spec_path=resolve_source_path(args.spec) if args.spec else None,
        flow_path=resolve_source_path(args.flow) if args.flow else None,
        restored_spec_path=resolve_source_path(args.restored_spec_out) if args.restored_spec_out else None,
    )
    result = register_skill_artifacts(spec, Path(args.skill_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
