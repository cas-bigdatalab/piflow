#!/usr/bin/env python3
import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Iterable


DEFAULT_OUTPUT_ROOT = "skills/generated"
LEGACY_OUTPUT_ROOTS = {
    "workspace/skills",
    "workspace/skills/generated",
    "flow-deepagents/workspace/skills",
    "flow-deepagents/workspace/skills/generated",
}
PARAM_ROLES = {"input_data", "output_data", "data"}
FRONTMATTER_KEYS = {
    "name",
    "name_zh",
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
CLASSIFICATION_FILE = Path(__file__).resolve().parents[4] / "docs" / "skill分类.txt"
STORAGE_SKILLS_DIR = Path(__file__).resolve().parents[4] / "storage" / "skills"
DEFAULT_CATEGORY = "其他"
DEFAULT_CATEGORY_ICON = "Other.png"
TAG_TO_CLASSIFICATION = {
    "清洗": "清洗",
    "校验": "校验",
    "去重": "去重",
    "格式转换": "格式转换",
    "标准化": "标准化",
    "过滤与筛选": "过滤与筛选",
    "增强": "增强",
    "流程控制": "流程控制",
    "输出": "输出",
    "设计创作": "设计创作",
    "输入": "输入",
    "其他": "其他",
}
CLASSIFICATION_ICON_ALIASES = {
    "清洗": "data-cleansing.png",
    "校验": "quality-control.png",
    "去重": "data-Aggregation.png",
    "格式转换": "simple-data-format.png",
    "标准化": "Mapping & Conversion.png",
    "过滤与筛选": "Text Analysis.png",
    "增强": "data-Aggregation.png",
    "流程控制": "Workflow & Pipeline.png",
    "输出": "Document Processing.png",
    "设计创作": "Design & Creative.png",
    "输入": "Document Processing.png",
    "其他": "Other.png",
}


def workspace_root() -> Path:
    # This script lives in <workspace>/skills/piflow-skill-generator/scripts.
    return Path(__file__).resolve().parents[3]


def workspace_relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def resolve_source_path(raw_path: str) -> Path:
    path = Path(str(raw_path))
    if path.is_absolute():
        return path
    for candidate in (Path.cwd() / path, workspace_root() / path):
        if candidate.exists():
            return candidate
    return Path.cwd() / path


def resolve_output_root(raw_output_root: str | None) -> Path:
    raw = (raw_output_root or DEFAULT_OUTPUT_ROOT).strip().replace("\\", "/")
    if raw in LEGACY_OUTPUT_ROOTS:
        raw = DEFAULT_OUTPUT_ROOT
    path = Path(raw)
    if path.is_absolute():
        return path
    # Normalize: strip "workspace/" prefix if user accidentally included it
    for prefix in ("workspace/", "flow-deepagents/workspace/"):
        if raw.startswith(prefix) and raw != prefix.strip("/"):
            raw = raw[len(prefix):]
            path = Path(raw)
            break
    if raw == DEFAULT_OUTPUT_ROOT or raw.startswith(f"{DEFAULT_OUTPUT_ROOT}/"):
        return workspace_root() / path
    # Any other relative path: resolve against workspace root
    return workspace_root() / path


def read_json(path: Path) -> dict:
    data = json.loads(read_text(path))
    if not isinstance(data, dict):
        raise ValueError("spec must be a JSON object")
    return data


def read_spec_input(*, spec_path: Path | None = None, flow_path: Path | None = None, restored_spec_path: Path | None = None) -> dict:
    if spec_path and flow_path:
        raise ValueError("provide either spec_path or flow_path, not both")
    if not spec_path and not flow_path:
        raise ValueError("either spec_path or flow_path is required")

    if spec_path:
        return read_json(spec_path)

    flow = read_json(flow_path)
    spec = restore_spec_from_flow(flow)
    if restored_spec_path:
        write_text(restored_spec_path, json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    return spec


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def safe_rel_path(raw_path: str, field_name: str) -> Path:
    path = Path(str(raw_path or ""))
    if not str(path) or path.is_absolute() or any(part in {"..", ""} for part in path.parts):
        raise ValueError(f"{field_name} must be a safe relative path: {raw_path}")
    return path


def classification_file() -> Path:
    return CLASSIFICATION_FILE


def storage_skills_dir() -> Path:
    return STORAGE_SKILLS_DIR


def as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def non_empty_text(value) -> str:
    return str(value or "").strip()


def slugify_name(value: str, default: str = "restored_skill") -> str:
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "").strip())
    text = re.sub(r"_+", "_", text).strip("._-")
    return text or default


def normalize_description(spec: dict) -> str:
    description = str(spec.get("description", "")).strip()
    triggers = [str(t).strip() for t in spec.get("triggers", []) if str(t).strip()]
    if triggers and all(token not in description for token in ("当用户", "触发", "Use when")):
        description = f"{description} 当用户提到{'、'.join(triggers)}等需求时使用此 skill。"
    return description


def normalize_restored_params(items, *, is_input: bool) -> list[dict]:
    params = []
    for item in as_list(items):
        if not isinstance(item, dict):
            continue
        name = non_empty_text(item.get("name"))
        description = non_empty_text(item.get("description")) or ("输入参数" if is_input else "输出参数")
        param = {
            "name": name,
            "type": non_empty_text(item.get("type")) or ("string" if is_input else "json_file"),
            "role": non_empty_text(item.get("role")) or ("input_data" if is_input else "output_data"),
            "description": description,
        }
        if is_input:
            param["required"] = bool(item.get("required", True))
            if "default" in item:
                param["default"] = item["default"]
        params.append(param)
    return params


def flow_task_block(flow: dict) -> dict:
    task = flow.get("task")
    return task if isinstance(task, dict) else {}


def flow_text(flow: dict, *keys: str) -> str:
    task = flow_task_block(flow)
    for key in keys:
        if key.startswith("task."):
            value = task.get(key.split(".", 1)[1])
        else:
            value = flow.get(key)
        text = non_empty_text(value)
        if text:
            return text
    return ""


def flow_list(flow: dict, *keys: str):
    task = flow_task_block(flow)
    for key in keys:
        if key.startswith("task."):
            value = task.get(key.split(".", 1)[1])
        else:
            value = flow.get(key)
        if value:
            return value
    return []


def normalize_restored_scripts(flow: dict) -> list[dict]:
    script_items = []
    primary_script = flow.get("script")
    if isinstance(primary_script, dict) and primary_script.get("path"):
        script_items.append(primary_script)
    for item in as_list(flow.get("scripts")):
        if isinstance(item, dict) and item.get("path"):
            script_items.append(item)
    return script_items


def normalize_processing_steps(flow: dict) -> list[str]:
    steps = [str(step).strip() for step in as_list(flow_list(flow, "processing_steps", "steps")) if str(step).strip()]
    nodes = [node for node in as_list(flow.get("nodes")) if isinstance(node, dict)]
    if nodes:
        node_steps = []
        for node in nodes:
            node_name = non_empty_text(node.get("node_name") or node.get("name"))
            skill_name = non_empty_text(node.get("skill_name"))
            if node_name or skill_name:
                summary = " / ".join(part for part in (node_name, skill_name) if part)
                node_steps.append(f"节点：{summary}")
        steps.extend(node_steps)
    return steps


def normalize_success_evidence(flow: dict):
    return flow.get("success_evidence") or flow.get("validation") or flow.get("output_structure") or {}


def restore_spec_from_flow(flow: dict) -> dict:
    if not isinstance(flow, dict):
        raise ValueError("flow summary must be a JSON object")

    name = slugify_name(flow_text(flow, "skill_name", "name", "task_name", "task.name"))
    title = flow_text(flow, "title", "task_name", "task.name") or name
    name_zh = non_empty_text(flow.get("skill_name_zh") or flow.get("name_zh") or title or name)
    task_description = flow_text(flow, "task_description", "description", "task.description")
    processing_steps = normalize_processing_steps(flow)
    script_items = normalize_restored_scripts(flow)
    references = [item for item in as_list(flow.get("references")) if isinstance(item, dict) and item.get("path")]
    examples = [item for item in as_list(flow.get("examples")) if isinstance(item, dict)]
    success_evidence = normalize_success_evidence(flow)

    description = task_description or f"基于已验证成功的处理流程恢复 {name} skill 草稿。"
    trigger_conditions = [
        "当一次真实处理流程已经跑通，并且用户希望将其封装为可复用 skill 时使用此技能。",
        "当现有技能库无法直接满足需求，但已经通过脚本或步骤成功完成任务，并希望回调式沉淀为 skill 时使用此技能。"
    ]
    if non_empty_text(flow.get("manual_trigger_hint")):
        trigger_conditions.insert(0, non_empty_text(flow["manual_trigger_hint"]))

    metadata = dict(flow.get("metadata") or {})
    metadata.update(
        {
            "restored_from_flow": True,
            "flow_task_name": flow_text(flow, "task_name", "task.name"),
            "flow_success_evidence": success_evidence or {},
        }
    )

    spec = {
        "name": name,
        "name_zh": name_zh,
        "title": title,
        "description": description,
        "version": non_empty_text(flow.get("version")) or "1.0.0",
        "category": non_empty_text(flow.get("category")) or "restored_flow",
        "tag": non_empty_text(flow.get("tag")) or "其他",
        "triggers": [item for item in as_list(flow.get("triggers")) if str(item).strip()],
        "trigger_conditions": trigger_conditions,
        "input_params": normalize_restored_params(flow_list(flow, "inputs", "input_params"), is_input=True),
        "output_params": normalize_restored_params(flow_list(flow, "outputs", "output_params"), is_input=False),
        "scripts": script_items,
        "references": references,
        "examples": examples,
        "processing_logic": processing_steps,
        "core_features": [str(item).strip() for item in as_list(flow.get("core_features")) if str(item).strip()],
        "supported_formats": [str(item).strip() for item in as_list(flow.get("supported_formats")) if str(item).strip()],
        "output_structure": flow.get("output_structure") or success_evidence or {},
        "output_examples": flow.get("output_examples") or success_evidence or {},
        "dependencies": [str(item).strip() for item in as_list(flow.get("dependencies")) if str(item).strip()],
        "metadata": metadata,
        "notes": [
            "本 skill 草稿由已验证成功的处理流程恢复生成，建议人工补齐命名、图标与触发表达。",
            "在回调式沉淀链路中，应优先复用已有脚本和成功证据，而不是重新手写实现。",
        ],
    }
    return spec


def parse_classification_sections(text: str) -> list[tuple[str, list[tuple[str, str]]]]:
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    current_name = ""
    current_items: list[tuple[str, str]] = []
    item_pattern = re.compile(r"^- \*\*(.+?)\*\*: (.+)$")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if current_name:
                sections.append((current_name, current_items))
            current_name = line[3:].strip()
            current_items = []
            continue
        match = item_pattern.match(line)
        if match and current_name:
            current_items.append((match.group(1).strip(), match.group(2).strip()))

    if current_name:
        sections.append((current_name, current_items))
    return sections


def load_classification_sections() -> list[tuple[str, list[tuple[str, str]]]]:
    path = classification_file()
    if not path.exists():
        return []
    return parse_classification_sections(read_text(path))


def known_classifications(sections: Iterable[tuple[str, list[tuple[str, str]]]]) -> set[str]:
    return {name for name, _ in sections if name}


def category_icon_filename(classification: str) -> str:
    return CLASSIFICATION_ICON_ALIASES.get(classification, DEFAULT_CATEGORY_ICON)


def infer_classification(spec: dict) -> str:
    sections = load_classification_sections()
    available = known_classifications(sections)
    candidates = [
        non_empty_text(spec.get("classification")),
        non_empty_text(spec.get("classification_name")),
        non_empty_text(spec.get("tag")),
        non_empty_text(spec.get("category")),
    ]
    for candidate in candidates:
        if candidate in available:
            return candidate
        mapped = TAG_TO_CLASSIFICATION.get(candidate)
        if mapped and (not available or mapped in available):
            return mapped
    return DEFAULT_CATEGORY if DEFAULT_CATEGORY in available or not available else sorted(available)[0]


def normalize_param(param: dict, *, is_input: bool) -> dict:
    item = dict(param)
    item["name"] = str(item.get("name", "")).strip()
    item["type"] = str(item.get("type", "string")).strip()
    item["description"] = str(item.get("description", "")).strip()
    item["role"] = item.get("role") or infer_role(item, is_input)
    if is_input:
        item["required"] = bool(item.get("required", False))
    return item


def infer_role(param: dict, is_input: bool) -> str:
    if not is_input:
        return "output_data"
    name = str(param.get("name", "")).lower()
    param_type = str(param.get("type", "")).lower()
    if name.startswith("output") or "output" in name:
        return "output_data"
    if name.startswith("input") or "input" in name:
        return "input_data"
    if param_type in {"file", "directory", "csv_file", "json_file", "xlsx_file", "pdf_file", "text_file"}:
        return "input_data"
    return "data"


def validate_spec(spec: dict) -> None:
    name = str(spec.get("name", "")).strip()
    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        raise ValueError("spec.name must be a safe folder name")
    if len(name) > 128:
        raise ValueError("spec.name is too long for PiFlow use")
    if not normalize_description(spec):
        raise ValueError("spec.description is required")

    for field_name, is_input in (("input_params", True), ("output_params", False)):
        params = spec.get(field_name, [])
        if not isinstance(params, list):
            raise ValueError(f"spec.{field_name} must be a list")
        for index, raw in enumerate(params):
            if not isinstance(raw, dict):
                raise ValueError(f"spec.{field_name}[{index}] must be an object")
            param = normalize_param(raw, is_input=is_input)
            for key in ("name", "type", "description"):
                if not param[key]:
                    raise ValueError(f"spec.{field_name}[{index}] missing {key}")
            if is_input and "required" not in raw:
                raise ValueError(f"spec.{field_name}[{index}] missing required")
            if param["role"] not in PARAM_ROLES:
                raise ValueError(f"spec.{field_name}[{index}].role must be one of {sorted(PARAM_ROLES)}")


def normalize_spec(spec: dict) -> dict:
    validate_spec(spec)
    normalized = dict(spec)
    normalized["description"] = normalize_description(spec)
    normalized["version"] = str(spec.get("version", "1.0.0"))
    normalized["name_zh"] = non_empty_text(spec.get("name_zh"))
    normalized["input_params"] = [normalize_param(p, is_input=True) for p in spec.get("input_params", [])]
    normalized["output_params"] = [normalize_param(p, is_input=False) for p in spec.get("output_params", [])]
    normalized["script_path"] = str(spec.get("script_path") or first_script_path(spec))
    normalized["command"] = str(spec.get("command") or command_from_spec(normalized)).strip()
    normalized["classification"] = infer_classification(normalized)
    return normalized


def build_rewrite_followup_suggestion(*, skill_name: str, skill_dir: str, rewrite_followup_hint: str = "") -> dict:
    message = non_empty_text(rewrite_followup_hint) or (
        "如果用户在 skill 生成完成后又提供了新的成功流程，可以询问是否要以新的流程为指引继续改写当前 skill。"
    )
    return {
        "skill_name": skill_name,
        "skill_dir": skill_dir,
        "message": message,
        "command": (
            f"python scripts/rewrite_piflow_skill.py --skill-dir {skill_dir} "
            "--flow path/to/new-flow-summary.json --restored-spec-out workspace/artifacts/rewrite-spec.json"
        ),
        "reference": "references/rewrite_followup_internal.md",
    }


def first_script_path(spec: dict) -> str:
    script = spec.get("script")
    if isinstance(script, dict) and script.get("path"):
        return str(script["path"])
    scripts = spec.get("scripts") or []
    if scripts and isinstance(scripts[0], dict) and scripts[0].get("path"):
        return str(scripts[0]["path"])
    return ""


def command_from_spec(spec: dict) -> str:
    script_path = spec.get("script_path") or first_script_path(spec)
    if not script_path:
        return ""
    tokens = ["python", script_path]
    for param in spec.get("input_params", []):
        name = param["name"]
        token = f"--{name} <{name}>"
        tokens.append(token if param.get("required") else f"[{token}]")
    return " ".join(tokens)


def command_template(spec: dict) -> list[str]:
    explicit = spec.get("command_template")
    if isinstance(explicit, list) and explicit:
        return [str(item) for item in explicit]
    tokens = []
    if spec.get("script_path"):
        tokens = ["python", "{script_path}"]
    for param in spec.get("input_params", []):
        tokens.extend([f"--{param['name']}", f"{{{param['name']}}}"])
    return tokens


def yaml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text and re.fullmatch(r"[A-Za-z0-9_./:@+\-]+", text) and text.lower() not in {"true", "false", "null"}:
        return text
    return json.dumps(text, ensure_ascii=False)


def yaml_lines(value, indent: int = 0) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{pad}- name: {yaml_scalar(item.get('name', ''))}")
                for key, val in item.items():
                    if key == "name":
                        continue
                    child = " " * (indent + 2)
                    if isinstance(val, (dict, list)):
                        lines.append(f"{child}{key}:")
                        lines.extend(yaml_lines(val, indent + 4))
                    else:
                        lines.append(f"{child}{key}: {yaml_scalar(val)}")
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return lines or [f"{pad}[]"]
    return [f"{pad}{yaml_scalar(value)}"]


def frontmatter(spec: dict) -> str:
    data = {
        "name": spec["name"],
        "description": spec["description"],
        "version": spec["version"],
    }
    if spec.get("name_zh"):
        data["name_zh"] = spec["name_zh"]
    for key in ("category", "tag", "allowed-tools", "compatibility", "license", "metadata"):
        src = "allowed_tools" if key == "allowed-tools" and "allowed_tools" in spec else key
        if src in spec:
            data[key] = spec[src]
    data["input_params"] = spec["input_params"]
    data["output_params"] = spec["output_params"]

    unexpected = set(data) - FRONTMATTER_KEYS
    if unexpected:
        raise ValueError(f"unexpected frontmatter keys: {', '.join(sorted(unexpected))}")
    return "---\n" + "\n".join(yaml_lines(data)) + "\n---\n"


def md_escape(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def param_table(params: list[dict], *, include_required: bool) -> str:
    if not params:
        return "无。"
    if include_required:
        rows = ["| 参数 | 类型 | 角色 | 必填 | 默认值 | 说明 |", "|------|------|------|------|--------|------|"]
        for p in params:
            rows.append(
                f"| {md_escape(p['name'])} | {md_escape(p['type'])} | {md_escape(p['role'])} | {'是' if p.get('required') else '否'} | {md_escape(p.get('default', '-'))} | {md_escape(p['description'])} |"
            )
    else:
        rows = ["| 参数 | 类型 | 角色 | 默认值 | 说明 |", "|------|------|------|--------|------|"]
        for p in params:
            rows.append(
                f"| {md_escape(p['name'])} | {md_escape(p['type'])} | {md_escape(p['role'])} | {md_escape(p.get('default', '-'))} | {md_escape(p['description'])} |"
            )
    return "\n".join(rows)


def json_block(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (dict, list)):
        return ["```json", json.dumps(value, ensure_ascii=False, indent=2), "```"]
    text = str(value).strip()
    return [text] if text else []


def add_bullets(lines: list[str], heading: str, items) -> None:
    values = [str(item).strip() for item in as_list(items) if str(item).strip()]
    if values:
        lines.extend([f"## {heading}", "", *[f"- {item}" for item in values], ""])


def add_text(lines: list[str], heading: str, content) -> None:
    block = json_block(content)
    if block:
        lines.extend([f"## {heading}", "", *block, ""])


def render_examples(examples) -> list[str]:
    if not examples:
        return []
    lines = ["## 示例", ""]
    for example in examples:
        if not isinstance(example, dict):
            lines.extend([str(example).strip(), ""])
            continue
        if example.get("title"):
            lines.append(f"### {example['title']}")
        if example.get("description"):
            lines.extend(["", str(example["description"]).strip()])
        if example.get("command"):
            lines.extend(["", "```bash", str(example["command"]).strip(), "```"])
        if example.get("input"):
            lines.extend(["", "输入：", *json_block(example["input"])])
        if example.get("output"):
            lines.extend(["", "输出：", *json_block(example["output"])])
        lines.append("")
    return lines


def render_body(spec: dict) -> str:
    lines = [
        f"# {spec.get('title') or spec['name']} 技能",
        "",
        "## 功能说明",
        "",
        str(spec.get("overview") or spec["description"]).strip(),
        "",
    ]

    triggers = [f"当用户提到“{t}”时优先考虑使用此技能。" for t in spec.get("triggers", [])]
    trigger_lines = []
    if spec.get("category"):
        trigger_lines.append(f"技能类别：{spec['category']}")
    if spec.get("tag"):
        trigger_lines.append(f"DAG 类型：{spec['tag']}")
    trigger_lines.extend(triggers)
    trigger_lines.extend(str(t).strip() for t in as_list(spec.get("trigger_conditions")) if str(t).strip())
    add_bullets(lines, "触发条件", trigger_lines)

    add_bullets(lines, "核心功能", spec.get("core_features"))
    add_bullets(lines, "处理逻辑", spec.get("processing_logic"))
    add_bullets(lines, "支持的文件格式", spec.get("supported_formats"))

    if spec.get("command"):
        lines.extend(["## 使用方法", "", "```bash", spec["command"], "```", ""])

    lines.extend([
        "## 参数说明",
        "",
        param_table(spec["input_params"], include_required=True),
        "",
        "## 输出参数",
        "",
        param_table(spec["output_params"], include_required=False),
        "",
    ])

    lines.extend(render_examples(spec.get("examples")))
    add_text(lines, "输入格式", spec.get("input_format"))
    add_text(lines, "输出结构", spec.get("output_structure"))
    if not spec.get("output_structure"):
        add_text(lines, "输出格式", spec.get("output_format"))
    add_text(lines, "输出示例", spec.get("output_examples"))

    refs = [str(item["path"]) for item in as_list(spec.get("references")) if isinstance(item, dict) and item.get("path")]
    add_bullets(lines, "参考资料", [f"需要详细规则或字段说明时读取 `{path}`。" for path in refs])
    add_text(lines, "实现说明", spec.get("implementation") or spec.get("implementation_notes"))
    add_bullets(lines, "依赖", spec.get("dependencies"))

    for section in as_list(spec.get("body_sections")):
        if isinstance(section, dict):
            add_text(lines, section.get("heading", "说明"), section.get("content", ""))
        else:
            add_text(lines, "说明", section)

    notes = spec.get("notes") or [
        "所有中文内容按 UTF-8 处理。",
        "调用脚本时只传入用户明确提供或有默认值的参数。",
        "输出文件路径应写入 PiFlow 工作区可访问的位置。",
    ]
    add_bullets(lines, "注意事项", notes)
    return "\n".join(lines).rstrip() + "\n"


def render_skill_json(spec: dict) -> str:
    data = {
        "name": spec["name"],
        "version": spec["version"],
        "description": spec["description"],
        "language": spec.get("language") or ("python" if spec.get("script_path", "").endswith(".py") else ""),
        "script_path": spec.get("script_path", ""),
        "entrypoint": spec.get("entrypoint") or (f"python {spec['script_path']}" if spec.get("script_path") else ""),
        "input_params": spec["input_params"],
        "output_params": spec["output_params"],
    }
    if spec.get("name_zh"):
        data["name_zh"] = spec["name_zh"]
    data["command_template"] = command_template(spec)
    for key in ("category", "tag"):
        if spec.get(key):
            data[key] = spec[key]
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def skill_display_description(spec: dict) -> str:
    return non_empty_text(spec.get("title_zh") or spec.get("name_zh") or spec.get("title") or spec["name"])


def update_classification_registry(spec: dict) -> None:
    path = classification_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    sections = load_classification_sections()
    section_name = spec["classification"]
    skill_name = spec["name"]
    description = skill_display_description(spec)

    if not sections:
        sections = [(section_name, [])]

    target_index = None
    for index, (name, _) in enumerate(sections):
        if name == section_name:
            target_index = index
            break
    if target_index is None:
        sections.append((section_name, []))
        target_index = len(sections) - 1

    # Remove existing registrations so the skill only appears once.
    cleaned_sections: list[tuple[str, list[tuple[str, str]]]] = []
    for name, items in sections:
        filtered = [(existing_name, existing_desc) for existing_name, existing_desc in items if existing_name != skill_name]
        cleaned_sections.append((name, filtered))
    sections = cleaned_sections

    section_items = list(sections[target_index][1])
    section_items.append((skill_name, description))
    section_items.sort(key=lambda item: item[0].lower())
    sections[target_index] = (section_name, section_items)

    lines: list[str] = []
    for index, (name, items) in enumerate(sections):
        if index:
            lines.append("")
        lines.append(f"## {name}")
        for item_name, item_desc in items:
            lines.append(f"- **{item_name}**: {item_desc}")
    write_text(path, "\n".join(lines).rstrip() + "\n")


def sync_storage_skill_icon(skill_dir: Path, spec: dict) -> None:
    storage_dir = storage_skills_dir()
    storage_dir.mkdir(parents=True, exist_ok=True)

    skill_icon = skill_dir / "assets" / "icon.png"
    if skill_icon.exists():
        shutil.copy2(skill_icon, storage_dir / f"{spec['name']}.png")

    section_name = spec["classification"]
    category_icon_path = storage_dir / category_icon_filename(section_name)
    if category_icon_path.exists():
        return

    alias_path = storage_dir / DEFAULT_CATEGORY_ICON
    if alias_path.exists():
        shutil.copy2(alias_path, category_icon_path)
        return

    fallback = storage_dir / DEFAULT_CATEGORY_ICON
    if fallback.exists():
        shutil.copy2(fallback, category_icon_path)


def backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.__backup__")


def prepare_file_backup(path: Path) -> Path | None:
    backup = backup_path(path)
    if backup.exists():
        if backup.is_dir():
            shutil.rmtree(backup)
        else:
            backup.unlink()

    if path.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        return backup
    return None


def restore_file_backup(path: Path, backup: Path | None) -> None:
    if path.exists():
        path.unlink()
    if backup and backup.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(backup), str(path))


def cleanup_file_backup(backup: Path | None) -> None:
    if backup and backup.exists():
        backup.unlink()


def resource_items(spec: dict, key: str) -> list[dict]:
    value = spec.get(key)
    if not value:
        return []
    items = [value] if isinstance(value, dict) else value
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError(f"spec.{key} must be an object or list of objects")
    return items


def copy_or_write(skill_dir: Path, item: dict, field_name: str, fallback_content: str | None = None) -> None:
    rel_path = safe_rel_path(item.get("path"), field_name)
    target = skill_dir / rel_path
    if item.get("source"):
        source = resolve_source_path(item["source"])
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            return
    if "content" in item or fallback_content is not None:
        write_text(target, str(item.get("content", fallback_content)))
        return
    if item.get("source"):
        raise FileNotFoundError(f"{field_name} source not found: {source}")
    raise ValueError(f"{field_name} item requires source or content: {item.get('path')}")


def script_template(spec: dict) -> str:
    lines = [
        "#!/usr/bin/env python3",
        "import argparse",
        "",
        "",
        "def main():",
        f"    parser = argparse.ArgumentParser(description={json.dumps(spec['description'], ensure_ascii=False)})",
    ]
    for param in spec["input_params"]:
        default = "" if "default" not in param else f", default={json.dumps(param['default'], ensure_ascii=False)}"
        lines.append(
            f"    parser.add_argument('--{param['name']}', required={str(bool(param.get('required')))}, help={json.dumps(param['description'], ensure_ascii=False)}{default})"
        )
    lines.extend([
        "    args = parser.parse_args()",
        "    _ = args",
        f"    raise NotImplementedError({json.dumps('Implement ' + spec['name'] + ' operator logic here.', ensure_ascii=False)})",
        "",
        "",
        'if __name__ == "__main__":',
        "    main()",
        "",
    ])
    return "\n".join(lines)


def write_resources(skill_dir: Path, spec: dict) -> None:
    if spec.get("icon") or spec.get("assets"):
        (skill_dir / "assets").mkdir(parents=True, exist_ok=True)
    if spec.get("icon"):
        icon = resolve_source_path(spec["icon"])
        if not icon.exists():
            raise FileNotFoundError(f"icon not found: {spec['icon']}")
        shutil.copy2(icon, skill_dir / "assets" / "icon.png")

    if isinstance(spec.get("script"), dict) and spec["script"].get("path"):
        copy_or_write(skill_dir, spec["script"], "script", script_template(spec))
    for item in resource_items(spec, "scripts"):
        copy_or_write(skill_dir, item, "scripts", script_template(spec))
    for key in ("references", "assets"):
        for item in resource_items(spec, key):
            copy_or_write(skill_dir, item, key)


def generate_skill_files(spec: dict, output_root: Path, overwrite: bool) -> dict:
    spec = normalize_spec(spec)
    skill_dir = output_root / spec["name"]
    backup_dir: Path | None = None

    if skill_dir.exists():
        if not overwrite:
            raise FileExistsError(f"skill already exists: {skill_dir}")
        backup_dir = skill_dir.with_name(f"{skill_dir.name}.__backup__")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.move(str(skill_dir), str(backup_dir))

    try:
        skill_dir.mkdir(parents=True)

        write_text(skill_dir / "SKILL.md", frontmatter(spec) + "\n" + render_body(spec))
        write_resources(skill_dir, spec)
        if spec.get("skill_json", True):
            write_text(skill_dir / "skill.json", render_skill_json(spec))
    except Exception:
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        if backup_dir and backup_dir.exists():
            shutil.move(str(backup_dir), str(skill_dir))
        raise

    if backup_dir and backup_dir.exists():
        shutil.rmtree(backup_dir)

    return {
        "skill_dir": workspace_relative_path(skill_dir),
        "skill_md": workspace_relative_path(skill_dir / "SKILL.md"),
        "skill_json": workspace_relative_path(skill_dir / "skill.json") if spec.get("skill_json", True) else "",
    }


def register_skill_artifacts(spec: dict, skill_dir: Path) -> dict:
    spec = normalize_spec(spec)
    classification_backup: Path | None = None
    skill_icon_backup: Path | None = None
    category_icon_backup: Path | None = None

    classification_path = classification_file()
    storage_dir = storage_skills_dir()
    skill_icon_path = storage_dir / f"{spec['name']}.png"
    category_icon_path = storage_dir / category_icon_filename(spec["classification"])

    try:
        classification_backup = prepare_file_backup(classification_path)
        skill_icon_backup = prepare_file_backup(skill_icon_path)
        category_icon_backup = prepare_file_backup(category_icon_path)

        update_classification_registry(spec)
        sync_storage_skill_icon(skill_dir, spec)
    except Exception:
        restore_file_backup(classification_path, classification_backup)
        restore_file_backup(skill_icon_path, skill_icon_backup)
        restore_file_backup(category_icon_path, category_icon_backup)
        raise

    cleanup_file_backup(classification_backup)
    cleanup_file_backup(skill_icon_backup)
    cleanup_file_backup(category_icon_backup)

    return {
        "classification_file": str(classification_path),
        "skill_icon_path": str(skill_icon_path),
        "category_icon_path": str(category_icon_path),
    }


def generate(spec: dict, output_root: Path, overwrite: bool) -> dict:
    spec = normalize_spec(spec)
    file_result = generate_skill_files(spec, output_root, overwrite)
    skill_dir = output_root / spec["name"]
    registration_result = register_skill_artifacts(spec, skill_dir)
    followup = build_rewrite_followup_suggestion(
        skill_name=spec["name"],
        skill_dir=file_result["skill_dir"],
        rewrite_followup_hint=non_empty_text(spec.get("rewrite_followup_hint")),
    )
    return {
        **file_result,
        **registration_result,
        "rewrite_followup_suggestion": followup,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate a PiFlow-compatible skill from a UTF-8 JSON spec.")
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
    result = generate(spec, resolve_output_root(args.output_root), args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
