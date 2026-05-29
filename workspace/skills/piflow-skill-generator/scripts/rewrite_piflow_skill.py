#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from generate_piflow_skill import (
    read_spec_input,
    resolve_output_root,
    resolve_source_path,
    restore_spec_from_flow,
    read_text,
    write_text,
    generate,
)


def load_existing_skill_name(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in existing skill dir: {skill_dir}")

    for line in read_text(skill_md).splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return skill_dir.name


def restore_rewrite_spec_from_flow(skill_dir: Path, flow: dict) -> dict:
    spec = restore_spec_from_flow(flow)
    existing_name = load_existing_skill_name(skill_dir)
    spec["name"] = existing_name

    metadata = dict(spec.get("metadata") or {})
    metadata.update(
        {
            "rewrite_existing_skill": True,
            "rewrite_target_skill": existing_name,
            "rewrite_target_dir": str(skill_dir),
        }
    )
    spec["metadata"] = metadata

    notes = list(spec.get("notes") or [])
    notes.append("如果当前 skill 已生成完成，且用户随后给出了新的可行流程，可询问是否按该流程对当前 skill 做一次改写。")
    notes.append("该改写链路默认复用原 skill 名称，并以 overwrite 方式重建目录。")
    spec["notes"] = notes
    return spec


def read_rewrite_input(*, skill_dir: Path, spec_path: Path | None = None, flow_path: Path | None = None, restored_spec_path: Path | None = None) -> dict:
    if spec_path:
        spec = read_spec_input(spec_path=spec_path)
        spec["name"] = load_existing_skill_name(skill_dir)
        metadata = dict(spec.get("metadata") or {})
        metadata.update(
            {
                "rewrite_existing_skill": True,
                "rewrite_target_skill": spec["name"],
                "rewrite_target_dir": str(skill_dir),
            }
        )
        spec["metadata"] = metadata
        if restored_spec_path:
            write_text(restored_spec_path, json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
        return spec

    if flow_path:
        flow = json.loads(read_text(flow_path))
        spec = restore_rewrite_spec_from_flow(skill_dir, flow)
        if restored_spec_path:
            write_text(restored_spec_path, json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
        return spec

    raise ValueError("either spec_path or flow_path is required")


def main():
    parser = argparse.ArgumentParser(
        description="Rewrite an existing PiFlow skill using a new spec or a newly validated workflow summary."
    )
    parser.add_argument("--skill-dir", required=True, help="Existing generated skill directory path")
    parser.add_argument("--spec", help="UTF-8 JSON rewrite spec path")
    parser.add_argument("--flow", help="UTF-8 JSON successful workflow summary path used as rewrite guidance")
    parser.add_argument("--restored-spec-out", help="Optional path to write restored rewrite spec")
    parser.add_argument("--output-root", default="skills", help="Skill output root relative to workspace")
    args = parser.parse_args()

    skill_dir = resolve_source_path(args.skill_dir)
    spec = read_rewrite_input(
        skill_dir=skill_dir,
        spec_path=resolve_source_path(args.spec) if args.spec else None,
        flow_path=resolve_source_path(args.flow) if args.flow else None,
        restored_spec_path=resolve_source_path(args.restored_spec_out) if args.restored_spec_out else None,
    )
    result = generate(spec, resolve_output_root(args.output_root), overwrite=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
