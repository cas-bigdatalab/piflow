#!/usr/bin/env python3
import argparse
import json

from generate_piflow_skill import read_json, resolve_source_path, restore_spec_from_flow, write_text


def main():
    parser = argparse.ArgumentParser(
        description="Restore a draft PiFlow skill spec from a validated successful workflow summary."
    )
    parser.add_argument("--flow", required=True, help="UTF-8 JSON file describing the successful workflow")
    parser.add_argument("--output", required=True, help="Output UTF-8 JSON spec path")
    args = parser.parse_args()

    flow = read_json(resolve_source_path(args.flow))
    spec = restore_spec_from_flow(flow)
    write_text(resolve_source_path(args.output), json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"spec_path": str(resolve_source_path(args.output)), "skill_name": spec["name"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
