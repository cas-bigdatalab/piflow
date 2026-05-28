#!/usr/bin/env python3
import argparse
import json

from generate_piflow_skill import read_json, resolve_output_root, resolve_source_path, generate_skill_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate PiFlow skill files only, without touching classification registry or storage icons."
    )
    parser.add_argument("--spec", required=True, help="UTF-8 JSON spec path")
    parser.add_argument("--output-root", default="skills", help="Skill output root relative to workspace")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    spec = read_json(resolve_source_path(args.spec))
    result = generate_skill_files(spec, resolve_output_root(args.output_root), args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
