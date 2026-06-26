#!/usr/bin/env python3
import argparse
import json

from generate_piflow_skill import DEFAULT_OUTPUT_ROOT, read_spec_input, resolve_output_root, resolve_source_path, generate_skill_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate PiFlow skill files only, without touching classification registry or storage icons."
    )
    parser.add_argument("--spec", help="UTF-8 JSON spec path")
    parser.add_argument("--flow", help="UTF-8 JSON successful workflow summary path")
    parser.add_argument("--restored-spec-out", help="Optional path to write restored spec when using --flow")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT, help="Skill output root relative to workspace")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    spec = read_spec_input(
        spec_path=resolve_source_path(args.spec) if args.spec else None,
        flow_path=resolve_source_path(args.flow) if args.flow else None,
        restored_spec_path=resolve_source_path(args.restored_spec_out) if args.restored_spec_out else None,
    )
    result = generate_skill_files(spec, resolve_output_root(args.output_root), args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
