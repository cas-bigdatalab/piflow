#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


try:
    import yaml
except ImportError:
    yaml = None


ALLOWED_KEYS = {
    "name",
    "description",
    "version",
    "category",
    "tag",
    "input_params",
    "output_params",
    "allowed-tools",
    "compatibility",
    "license",
    "metadata",
}

TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".csv",
    ".tsv",
}


def fail(message: str) -> tuple[bool, str]:
    return False, message


def load_yaml_file(path: Path) -> tuple[bool, str | dict]:
    if yaml is None:
        return fail("PyYAML is required for validation")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return fail(f"{path} is not valid UTF-8: {exc}")
    try:
        data = yaml.safe_load(text)
    except Exception as exc:
        return fail(f"{path} YAML is invalid: {exc}")
    if not isinstance(data, dict):
        return fail(f"{path} must be a mapping")
    return True, data


def load_frontmatter(skill_md: Path) -> tuple[bool, str | dict]:
    try:
        content = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return fail(f"SKILL.md is not valid UTF-8: {exc}")

    if not content.startswith("---\n"):
        return fail("SKILL.md must start with YAML frontmatter")

    match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not match:
        return fail("SKILL.md frontmatter delimiter is invalid")

    if yaml is None:
        return fail("PyYAML is required for validation")

    try:
        data = yaml.safe_load(match.group(1))
    except Exception as exc:
        return fail(f"frontmatter YAML is invalid: {exc}")

    if not isinstance(data, dict):
        return fail("frontmatter must be a mapping")
    return True, data


def validate_params(params, field_name: str) -> tuple[bool, str]:
    if params is None:
        return True, "ok"
    if not isinstance(params, list):
        return fail(f"{field_name} must be a list")
    seen = set()
    for index, item in enumerate(params):
        if not isinstance(item, dict):
            return fail(f"{field_name}[{index}] must be a mapping")
        for required_key in ("name", "type", "description"):
            if required_key not in item or not str(item[required_key]).strip():
                return fail(f"{field_name}[{index}] missing {required_key}")
        name = str(item["name"])
        if name in seen:
            return fail(f"{field_name}[{index}] duplicates parameter name: {name}")
        seen.add(name)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            return fail(f"{field_name}[{index}] has unsafe parameter name: {name}")
        if field_name == "input_params":
            if "required" not in item:
                return fail(f"{field_name}[{index}] missing required")
            if not isinstance(item["required"], bool):
                return fail(f"{field_name}[{index}].required must be boolean")
        if "role" in item and str(item["role"]) not in {"input_data", "output_data", "data"}:
            return fail(f"{field_name}[{index}].role must be input_data, output_data, or data")
    return True, "ok"


def load_json_file(path: Path) -> tuple[bool, str | dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return fail(f"{path} is not valid UTF-8: {exc}")
    try:
        data = json.loads(text)
    except Exception as exc:
        return fail(f"{path} JSON is invalid: {exc}")
    if not isinstance(data, dict):
        return fail(f"{path} must be a JSON object")
    return True, data


def validate_agents_openai(skill_dir: Path, skill_name: str) -> tuple[bool, str]:
    agents = skill_dir / "agents" / "openai.yaml"
    if not agents.exists():
        return True, "ok"

    ok, data_or_message = load_yaml_file(agents)
    if not ok:
        return False, str(data_or_message)
    data = data_or_message

    interface = data.get("interface")
    if not isinstance(interface, dict):
        return fail("agents/openai.yaml must contain interface mapping")

    for key in ("display_name", "short_description", "default_prompt"):
        if key not in interface or not isinstance(interface[key], str) or not interface[key].strip():
            return fail(f"agents/openai.yaml interface.{key} must be a non-empty string")

    if f"${skill_name}" not in interface["default_prompt"]:
        return fail(f"agents/openai.yaml interface.default_prompt must mention ${skill_name}")

    for icon_key in ("icon_small", "icon_large"):
        if icon_key in interface:
            icon_path = skill_dir / interface[icon_key]
            if not icon_path.exists():
                return fail(f"agents/openai.yaml interface.{icon_key} target does not exist: {interface[icon_key]}")

    brand_color = interface.get("brand_color")
    if brand_color is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(brand_color)):
        return fail("agents/openai.yaml interface.brand_color must be a #RRGGBB value")

    return True, "ok"


def validate_text_files_utf8(skill_dir: Path) -> tuple[bool, str]:
    for path in skill_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                return fail(f"{path.relative_to(skill_dir)} is not valid UTF-8: {exc}")
    return True, "ok"


def validate_resource_layout(skill_dir: Path) -> tuple[bool, str]:
    for dirname in ("scripts", "references", "assets", "agents"):
        path = skill_dir / dirname
        if path.exists() and not path.is_dir():
            return fail(f"{dirname} must be a directory")

    for path in skill_dir.rglob("*"):
        if path.is_file() and path.name.lower() in {
            "readme.md",
            "installation_guide.md",
            "quick_reference.md",
            "changelog.md",
        }:
            return fail(f"extraneous documentation file is not allowed: {path.relative_to(skill_dir)}")
    return True, "ok"


def validate_skill_json(skill_dir: Path, frontmatter: dict) -> tuple[bool, str]:
    skill_json = skill_dir / "skill.json"
    if not skill_json.exists():
        return True, "ok"

    ok, data_or_message = load_json_file(skill_json)
    if not ok:
        return False, str(data_or_message)
    data = data_or_message

    for key in ("name", "version", "description", "language", "script_path", "entrypoint", "input_params", "output_params"):
        if key not in data:
            return fail(f"skill.json missing {key}")

    if data["name"] != frontmatter["name"]:
        return fail("skill.json name must match SKILL.md frontmatter name")

    if "version" in frontmatter and str(data["version"]) != str(frontmatter["version"]):
        return fail("skill.json version must match SKILL.md frontmatter version")

    script_path = str(data.get("script_path") or "")
    if script_path:
        target = skill_dir / script_path
        if not target.exists():
            return fail(f"skill.json script_path target does not exist: {script_path}")

    entrypoint = str(data.get("entrypoint") or "")
    if script_path and script_path not in entrypoint:
        return fail("skill.json entrypoint should include script_path")

    for field_name in ("input_params", "output_params"):
        params = data.get(field_name)
        if not isinstance(params, list):
            return fail(f"skill.json {field_name} must be a list")
        for index, item in enumerate(params):
            if not isinstance(item, dict):
                return fail(f"skill.json {field_name}[{index}] must be a mapping")
            for key in ("name", "role", "type", "description"):
                if key not in item or not str(item[key]).strip():
                    return fail(f"skill.json {field_name}[{index}] missing {key}")
            if item["role"] not in {"input_data", "output_data", "data"}:
                return fail(f"skill.json {field_name}[{index}].role is invalid")
            if field_name == "input_params" and "required" not in item:
                return fail(f"skill.json {field_name}[{index}] missing required")

    command_template = data.get("command_template")
    if command_template is not None:
        if not isinstance(command_template, list) or not all(isinstance(item, str) for item in command_template):
            return fail("skill.json command_template must be a list of strings")

    return True, "ok"


def validate(skill_dir: Path) -> tuple[bool, str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return fail("SKILL.md not found")

    ok, data_or_message = load_frontmatter(skill_md)
    if not ok:
        return False, str(data_or_message)
    data = data_or_message

    unexpected = set(data) - ALLOWED_KEYS
    if unexpected:
        return fail(f"unexpected frontmatter keys: {', '.join(sorted(unexpected))}")

    for key in ("name", "description"):
        if key not in data or not isinstance(data[key], str) or not data[key].strip():
            return fail(f"{key} must be a non-empty string")

    for key in ("version", "category", "tag"):
        if key in data and (not isinstance(data[key], str) or not data[key].strip()):
            return fail(f"{key} must be a non-empty string when present")

    if data["name"] != skill_dir.name:
        return fail(f"frontmatter name must match folder name: {skill_dir.name}")

    if len(data["description"].strip()) < 30:
        return fail("description is too short to be trigger-rich")

    for field_name in ("input_params", "output_params"):
        ok, message = validate_params(data.get(field_name), field_name)
        if not ok:
            return False, message

    for checker in (
        validate_resource_layout,
        validate_text_files_utf8,
    ):
        ok, message = checker(skill_dir)
        if not ok:
            return False, message

    ok, message = validate_agents_openai(skill_dir, data["name"])
    if not ok:
        return False, message

    ok, message = validate_skill_json(skill_dir, data)
    if not ok:
        return False, message

    icon = skill_dir / "assets" / "icon.png"
    if not icon.exists():
        print("warning: assets/icon.png not found; PiFlow will use the common icon", file=sys.stderr)

    return True, "PiFlow skill is valid"


def main():
    parser = argparse.ArgumentParser(description="Validate a PiFlow-compatible skill folder.")
    parser.add_argument("skill_dir")
    args = parser.parse_args()
    ok, message = validate(Path(args.skill_dir))
    print(message)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
