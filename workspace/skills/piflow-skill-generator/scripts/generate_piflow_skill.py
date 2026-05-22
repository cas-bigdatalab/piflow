#!/usr/bin/env python3
import argparse
import json
import re
import shutil
from pathlib import Path


PIFLOW_FRONTMATTER_KEYS = {
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

def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("spec must be a JSON object")
    return data


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def quote_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "":
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_./:@+\-]+", text) and text.lower() not in {"true", "false", "null"}:
        return text
    return json.dumps(text, ensure_ascii=False)


def emit_yaml(value, indent=0) -> list[str]:
    pad = " " * indent
    lines = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(emit_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {quote_scalar(item)}")
    elif isinstance(value, list):
        if not value:
            lines.append(f"{pad}[]")
        for item in value:
            if isinstance(item, dict):
                name = item.get("name")
                if name is not None:
                    lines.append(f"{pad}- name: {quote_scalar(name)}")
                    remaining = [(key, val) for key, val in item.items() if key != "name"]
                else:
                    lines.append(f"{pad}-")
                    remaining = list(item.items())
                child_indent = indent + (2 if name is None else 2)
                for key, val in remaining:
                    if isinstance(val, (dict, list)):
                        lines.append(f"{' ' * child_indent}{key}:")
                        lines.extend(emit_yaml(val, child_indent + 2))
                    else:
                        lines.append(f"{' ' * child_indent}{key}: {quote_scalar(val)}")
            elif isinstance(item, list):
                lines.append(f"{pad}-")
                lines.extend(emit_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {quote_scalar(item)}")
    else:
        lines.append(f"{pad}{quote_scalar(value)}")
    return lines


def safe_relative_path(raw_path: str, field_name: str) -> Path:
    if not raw_path or not str(raw_path).strip():
        raise ValueError(f"{field_name} path is required")
    path = Path(str(raw_path))
    if path.is_absolute() or any(part in {"..", ""} for part in path.parts):
        raise ValueError(f"{field_name} must be a safe relative path: {raw_path}")
    return path


def normalize_description(spec: dict) -> str:
    description = str(spec.get("description", "")).strip()
    triggers = [str(t).strip() for t in spec.get("triggers", []) if str(t).strip()]
    if triggers:
        trigger_text = "、".join(triggers)
        if "当用户" not in description and "触发" not in description and "Use when" not in description:
            description = f"{description} 当用户提到{trigger_text}等需求时使用此 skill。"
    return description


def validate_name(name: str) -> None:
    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        raise ValueError("spec.name must be a safe folder name")
    if len(name) > 128:
        raise ValueError("spec.name is too long for PiFlow use")


def validate_params(params, field_name: str) -> None:
    if params is None:
        return
    if not isinstance(params, list):
        raise ValueError(f"spec.{field_name} must be a list")
    for index, item in enumerate(params):
        if not isinstance(item, dict):
            raise ValueError(f"spec.{field_name}[{index}] must be an object")
        for required_key in ("name", "type", "description"):
            if not str(item.get(required_key, "")).strip():
                raise ValueError(f"spec.{field_name}[{index}] missing {required_key}")
        if field_name == "input_params" and "required" not in item:
            raise ValueError(f"spec.{field_name}[{index}] missing required")
        if "role" in item and str(item["role"]) not in {"input_data", "output_data", "data"}:
            raise ValueError(f"spec.{field_name}[{index}].role must be input_data, output_data, or data")


def validate_spec(spec: dict) -> None:
    if "name" not in spec:
        raise ValueError("spec.name is required")
    if not normalize_description(spec):
        raise ValueError("spec.description is required")
    validate_name(str(spec["name"]))
    validate_params(spec.get("input_params", []), "input_params")
    validate_params(spec.get("output_params", []), "output_params")


def frontmatter_for(spec: dict) -> dict:
    fm = {
        "name": spec["name"],
        "description": normalize_description(spec),
    }
    for key in ("version", "category", "tag"):
        if key in spec:
            fm[key] = spec[key]
    for src, dst in (("allowed_tools", "allowed-tools"), ("allowed-tools", "allowed-tools")):
        if src in spec:
            fm[dst] = spec[src]

    metadata = {}
    if isinstance(spec.get("metadata"), dict):
        metadata.update(spec["metadata"])
    if spec.get("category") and "category" not in metadata:
        metadata["category"] = spec["category"]

    for key in ("compatibility", "license"):
        if key in spec:
            fm[key] = spec[key]
    if metadata:
        fm["metadata"] = metadata

    fm["input_params"] = spec.get("input_params", [])
    fm["output_params"] = spec.get("output_params", [])
    return fm


def render_frontmatter(fm: dict) -> str:
    unexpected = set(fm) - PIFLOW_FRONTMATTER_KEYS
    if unexpected:
        raise ValueError(f"unexpected frontmatter keys: {', '.join(sorted(unexpected))}")
    return "---\n" + "\n".join(emit_yaml(fm)) + "\n---\n"


def md_escape(value) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def param_table(params: list[dict], include_required: bool = True) -> str:
    if not params:
        return "无。\n"
    if include_required:
        has_role = any("role" in p for p in params)
        if has_role:
            rows = ["| 参数 | 类型 | 角色 | 必填 | 默认值 | 说明 |", "|------|------|------|------|--------|------|"]
        else:
            rows = ["| 参数 | 类型 | 必填 | 默认值 | 说明 |", "|------|------|------|--------|------|"]
        for p in params:
            required = "是" if p.get("required") else "否"
            default = p.get("default", "-")
            if has_role:
                rows.append(
                    f"| {md_escape(p.get('name', ''))} | {md_escape(p.get('type', ''))} | {md_escape(p.get('role', '-'))} | {required} | {md_escape(default)} | {md_escape(p.get('description', ''))} |"
                )
            else:
                rows.append(
                    f"| {md_escape(p.get('name', ''))} | {md_escape(p.get('type', ''))} | {required} | {md_escape(default)} | {md_escape(p.get('description', ''))} |"
                )
    else:
        has_role = any("role" in p or "default" in p for p in params)
        if has_role:
            rows = ["| 参数 | 类型 | 角色 | 默认值 | 说明 |", "|------|------|------|--------|------|"]
        else:
            rows = ["| 参数 | 类型 | 说明 |", "|------|------|------|"]
        for p in params:
            if has_role:
                rows.append(
                    f"| {md_escape(p.get('name', ''))} | {md_escape(p.get('type', ''))} | {md_escape(p.get('role', '-'))} | {md_escape(p.get('default', '-'))} | {md_escape(p.get('description', ''))} |"
                )
            else:
                rows.append(
                    f"| {md_escape(p.get('name', ''))} | {md_escape(p.get('type', ''))} | {md_escape(p.get('description', ''))} |"
                )
    return "\n".join(rows) + "\n"


def command_from_spec(spec: dict) -> str:
    if spec.get("command"):
        return str(spec["command"]).strip()
    script = spec.get("script") or {}
    script_path = script.get("path") if isinstance(script, dict) else None
    scripts = spec.get("scripts") or []
    if not script_path and scripts and isinstance(scripts[0], dict):
        script_path = scripts[0].get("path")
    if not script_path:
        return ""
    required = []
    optional = []
    for p in spec.get("input_params", []):
        flag = f"--{p.get('name')}"
        token = f"<{p.get('name')}>"
        if p.get("required"):
            required.append(f"{flag} {token}")
        else:
            optional.append(f"[{flag} {token}]")
    return "python " + script_path + (" " + " ".join(required + optional) if required or optional else "")


def script_path_from_spec(spec: dict) -> str:
    script = spec.get("script") or {}
    if isinstance(script, dict) and script.get("path"):
        return str(script["path"])
    scripts = spec.get("scripts") or []
    if scripts and isinstance(scripts[0], dict) and scripts[0].get("path"):
        return str(scripts[0]["path"])
    command = command_from_spec(spec)
    match = re.search(r"python\s+([^\s]+\.py)", command)
    return match.group(1) if match else ""


def command_template_from_spec(spec: dict, script_path: str) -> list[str]:
    template = spec.get("command_template")
    if isinstance(template, list) and template:
        return [str(item) for item in template]
    if not script_path:
        return []
    tokens = ["python", "{script_path}"]
    for param in spec.get("input_params", []):
        name = param.get("name")
        if not name:
            continue
        tokens.extend([f"--{name}", f"{{{name}}}"])
    return tokens


def render_format_block(value, default_format: str = "json") -> list[str]:
    if value is None:
        return []
    if isinstance(value, (dict, list)):
        return [f"```{default_format}", json.dumps(value, ensure_ascii=False, indent=2), "```"]
    text = str(value).strip()
    if not text:
        return []
    return [text]


def resource_paths(spec: dict, key: str) -> list[str]:
    resources = spec.get(key) or []
    if isinstance(resources, dict):
        resources = [resources]
    paths = []
    for item in resources:
        if isinstance(item, dict) and item.get("path"):
            paths.append(str(item["path"]))
    return paths


def render_body(spec: dict) -> str:
    title = spec.get("title") or spec["name"]
    overview = spec.get("overview") or spec.get("description", "")
    triggers = [str(t).strip() for t in spec.get("triggers", []) if str(t).strip()]
    body_sections = spec.get("body_sections") or []
    dependencies = spec.get("dependencies") or []
    examples = spec.get("examples") or []
    command = command_from_spec(spec)
    reference_paths = resource_paths(spec, "references")

    lines = [f"# {title}", "", "## 功能概述", "", str(overview).strip(), ""]

    if triggers or spec.get("category"):
        lines.extend(["## 适用场景", ""])
        if spec.get("category"):
            lines.append(f"- 技能类别：{spec['category']}")
        for trigger in triggers:
            lines.append(f"- 当用户提到“{trigger}”时优先考虑使用此技能。")
        lines.append("")

    lines.extend(
        [
            "## 核心参数",
            "",
            param_table(spec.get("input_params", [])).rstrip(),
            "",
            "## 输出参数",
            "",
            param_table(spec.get("output_params", []), include_required=False).rstrip(),
            "",
        ]
    )

    if command:
        lines.extend(["## 使用方法", "", "```bash", command, "```", ""])

    if spec.get("input_format") or spec.get("output_format"):
        lines.extend(["## 输入输出格式", ""])
        if spec.get("input_format"):
            lines.extend(["### 输入格式", "", *render_format_block(spec.get("input_format")), ""])
        if spec.get("output_format"):
            lines.extend(["### 输出格式", "", *render_format_block(spec.get("output_format")), ""])

    if reference_paths:
        lines.extend(["## 参考资料", ""])
        for path in reference_paths:
            lines.append(f"- 需要详细规则或字段说明时读取 `{path}`。")
        lines.append("")

    implementation = spec.get("implementation") or spec.get("implementation_notes")
    if implementation:
        lines.extend(["## 实现说明", "", str(implementation).strip(), ""])

    if examples:
        lines.extend(["## 示例", ""])
        for item in examples:
            if not isinstance(item, dict):
                lines.extend(["### 示例", "", str(item).strip(), ""])
                continue
            lines.append(f"### {item.get('title', '示例')}")
            if item.get("description"):
                lines.extend(["", str(item["description"]).strip()])
            if item.get("command"):
                lines.extend(["", "```bash", str(item["command"]).strip(), "```"])
            if item.get("input"):
                lines.extend(["", "输入：", "```json", json.dumps(item["input"], ensure_ascii=False, indent=2), "```"])
            if item.get("output"):
                lines.extend(["", "输出：", "```json", json.dumps(item["output"], ensure_ascii=False, indent=2), "```"])
            lines.append("")

    if dependencies:
        lines.extend(["## 依赖", ""])
        for dep in dependencies:
            lines.append(f"- {dep}")
        lines.append("")

    for section in body_sections:
        if isinstance(section, dict):
            heading = section.get("heading", "说明")
            content = section.get("content", "")
        else:
            heading = "说明"
            content = section
        lines.extend([f"## {heading}", "", str(content).strip(), ""])

    notes = spec.get("notes") or []
    lines.extend(["## 注意事项", ""])
    if notes:
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.extend(
            [
                "- 所有中文内容按 UTF-8 处理。",
                "- 调用脚本时只传入用户明确提供或有默认值的参数。",
                "- 输出文件路径应写入 PiFlow 工作区可访问的位置。",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def agents_config(spec: dict) -> dict:
    raw = spec.get("agents_openai")
    if isinstance(raw, dict):
        config = dict(raw)
    else:
        config = {}
    for key in ("display_name", "short_description", "default_prompt", "brand_color"):
        if key in spec and key not in config:
            config[key] = spec[key]
    return config


def write_agents_openai(skill_dir: Path, spec: dict) -> None:
    config = agents_config(spec)
    display_name = config.get("display_name") or spec.get("title") or spec["name"]
    short_description = config.get("short_description") or normalize_description(spec)[:84]
    default_prompt = config.get("default_prompt") or f"Use ${spec['name']} to complete the requested PiFlow task."
    if f"${spec['name']}" not in default_prompt:
        default_prompt = f"Use ${spec['name']} to {default_prompt}"

    interface = {
        "display_name": display_name,
        "short_description": short_description,
    }
    if (skill_dir / "assets" / "icon.png").exists() or spec.get("icon"):
        interface["icon_small"] = "./assets/icon.png"
        interface["icon_large"] = "./assets/icon.png"
    if config.get("brand_color"):
        interface["brand_color"] = config["brand_color"]
    interface["default_prompt"] = default_prompt

    lines = ["interface:"]
    for key, value in interface.items():
        lines.append(f"  {key}: {json.dumps(str(value), ensure_ascii=False)}")
    write_text(skill_dir / "agents" / "openai.yaml", "\n".join(lines) + "\n")


def skill_json_param(param: dict, is_input: bool) -> dict:
    item = {
        "name": param.get("name", ""),
        "role": param.get("role") or infer_param_role(param, is_input),
        "type": param.get("type", "string"),
        "description": param.get("description", ""),
    }
    if is_input:
        item["required"] = bool(param.get("required", False))
    if "default" in param:
        item["default"] = param["default"]
    return item


def infer_param_role(param: dict, is_input: bool) -> str:
    if not is_input:
        return "output_data"
    name = str(param.get("name", "")).lower()
    param_type = str(param.get("type", "")).lower()
    if name.startswith("output") or "output" in name or param_type.endswith("_file"):
        return "output_data"
    if name.startswith("input") or "input" in name or param_type in {"file", "csv_file", "json_file", "xlsx_file", "pdf_file", "text_file", "directory"}:
        return "input_data"
    return "data"


def write_skill_json(skill_dir: Path, spec: dict) -> None:
    script_path = spec.get("script_path") or script_path_from_spec(spec)
    entrypoint = spec.get("entrypoint") or (f"python {script_path}" if script_path else command_from_spec(spec))
    command_template = command_template_from_spec(spec, script_path)
    data = {
        "name": spec["name"],
        "version": str(spec.get("version", "1.0.0")),
        "description": normalize_description(spec),
        "language": spec.get("language") or ("python" if script_path.endswith(".py") else ""),
        "script_path": script_path,
        "entrypoint": entrypoint,
        "input_params": [skill_json_param(p, True) for p in spec.get("input_params", [])],
        "output_params": [skill_json_param(p, False) for p in spec.get("output_params", [])],
    }
    if command_template:
        data["command_template"] = command_template
    if spec.get("category"):
        data["category"] = spec["category"]
    if spec.get("tag"):
        data["tag"] = spec["tag"]
    write_text(skill_dir / "skill.json", json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def copy_or_write_file(skill_dir: Path, item: dict, field_name: str) -> None:
    rel_path = safe_relative_path(item.get("path"), field_name)
    target = skill_dir / rel_path
    if item.get("source"):
        source = Path(item["source"])
        if not source.exists():
            raise FileNotFoundError(f"{field_name} source not found: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    elif "content" in item:
        write_text(target, str(item["content"]))
    else:
        raise ValueError(f"{field_name} item requires source or content: {item.get('path')}")


def normalize_items(spec: dict, key: str) -> list[dict]:
    value = spec.get(key)
    if not value:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        if not all(isinstance(item, dict) for item in value):
            raise ValueError(f"spec.{key} must contain objects")
        return value
    raise ValueError(f"spec.{key} must be an object or list")


def copy_or_write_resources(skill_dir: Path, spec: dict) -> None:
    if spec.get("icon") or spec.get("assets"):
        (skill_dir / "assets").mkdir(parents=True, exist_ok=True)

    icon = spec.get("icon")
    if icon:
        icon_path = Path(icon)
        if icon_path.exists():
            shutil.copy2(icon_path, skill_dir / "assets" / "icon.png")
        else:
            raise FileNotFoundError(f"icon not found: {icon}")

    script = spec.get("script")
    if isinstance(script, dict) and script.get("path"):
        item = dict(script)
        if "content" not in item and "source" not in item:
            item["content"] = script_template(spec)
        copy_or_write_file(skill_dir, item, "script")

    for item in normalize_items(spec, "scripts"):
        if "content" not in item and "source" not in item:
            item = dict(item)
            item["content"] = script_template(spec)
        copy_or_write_file(skill_dir, item, "scripts")

    for item in normalize_items(spec, "references"):
        copy_or_write_file(skill_dir, item, "references")

    for item in normalize_items(spec, "assets"):
        copy_or_write_file(skill_dir, item, "assets")


def py_string(value) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def script_template(spec: dict) -> str:
    lines = [
        "#!/usr/bin/env python3",
        "import argparse",
        "",
        "",
        "def main():",
        f"    parser = argparse.ArgumentParser(description={py_string(spec.get('description', spec['name']))})",
    ]
    for p in spec.get("input_params", []):
        required = "True" if p.get("required") else "False"
        default = p.get("default")
        default_part = "" if default is None else f", default={py_string(default)}"
        lines.append(
            f"    parser.add_argument('--{p.get('name')}', required={required}{default_part}, help={py_string(p.get('description', ''))})"
        )
    lines.extend(
        [
            "    args = parser.parse_args()",
            "    _ = args",
            f"    raise NotImplementedError({py_string('Implement ' + str(spec['name']) + ' operator logic here.')})",
            "",
            "",
            'if __name__ == "__main__":',
            "    main()",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate a PiFlow-compatible skill from a UTF-8 JSON spec.")
    parser.add_argument("--spec", required=True, help="UTF-8 JSON spec path")
    parser.add_argument("--output-root", default="flow-deepagents/workspace/skills", help="Skill output root")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = read_json(spec_path)
    validate_spec(spec)

    output_root = Path(args.output_root)
    skill_dir = output_root / spec["name"]
    if skill_dir.exists():
        if not args.overwrite:
            raise FileExistsError(f"skill already exists: {skill_dir}")
        shutil.rmtree(skill_dir)
    skill_dir.mkdir(parents=True)

    fm = frontmatter_for(spec)
    content = render_frontmatter(fm) + "\n" + render_body(spec)
    write_text(skill_dir / "SKILL.md", content)
    copy_or_write_resources(skill_dir, spec)
    if spec.get("skill_json", True):
        write_skill_json(skill_dir, spec)
    if spec.get("agents_openai"):
        write_agents_openai(skill_dir, spec)

    print(json.dumps({"skill_dir": str(skill_dir), "skill_md": str(skill_dir / "SKILL.md")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
