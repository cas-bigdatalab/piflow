import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import get_type_hints

import yaml
from pydantic import create_model

from infra.config_loader import get_settings
from tools.core.base import ToolSpec
from tools.core.registry import registry


log = logging.getLogger("flow.skill_loader")


class SkillLoader:

    def __init__(self):
        settings = get_settings()

        # skills 搜索路径
        self.skill_paths = settings.skills.paths
        # 已加载 skill metadata
        self.skills = []

    # -----------------------------
    # 自动生成 args_schema
    # -----------------------------
    def _build_args_schema(self, func):
        sig = inspect.signature(func)
        fields = {}
        try:
            resolved_hints = get_type_hints(func, globalns=func.__globals__, localns=func.__globals__)
        except Exception:
            resolved_hints = {}

        for name, param in sig.parameters.items():
            annotation = resolved_hints.get(name, param.annotation)
            if annotation is inspect._empty:
                annotation = str

            default = ...
            if param.default is not inspect._empty:
                default = param.default

            fields[name] = (annotation, default)

        model = create_model(
            f"{func.__name__}_Args",
            **fields
        )
        return model

    # -----------------------------
    # 扫描 SKILL.md
    # -----------------------------
    def discover(self):
        discovered = []
        log.info("scanning skill paths")

        for path in self.skill_paths:
            p = Path(path)
            log.info("checking skill path=%s", p)

            if not p.exists():
                log.warning("skill path not found path=%s", p)
                continue

            for skill_dir in p.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    log.info("found skill dir=%s", skill_dir.name)
                    discovered.append(skill_file)

        return discovered

    # -----------------------------
    # 加载 python tools
    # -----------------------------
    def _load_python_tools(self, skill_dir, skill_meta):
        log.info("scanning python files skill_dir=%s", skill_dir)

        sys.path.insert(0, str(skill_dir))

        py_files = [
            f for f in skill_dir.rglob("*.py")
            if f.name != "__init__.py"
        ]

        if not py_files:
            log.warning("no python files found skill_dir=%s", skill_dir)
            return

        allowed_tools = skill_meta.get("allowed-tools", [])

        for py_file in py_files:
            module_name = f"skill_{skill_dir.name}_{py_file.stem}"
            log.info("loading module file=%s", py_file)

            try:
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    py_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                log.info("module loaded name=%s", module_name)

            except Exception as e:
                log.error("failed loading module file=%s error=%s", py_file, e)
                continue

            found_function = False

            for name, obj in inspect.getmembers(module):
                if not inspect.isfunction(obj):
                    continue

                # 只允许当前模块函数
                if obj.__module__ != module.__name__:
                    continue

                # 如果 SKILL.md 指定 allowed-tools，则必须匹配
                if allowed_tools and name not in allowed_tools:
                    continue

                tool_name = f"{skill_dir.name}.{name}"

                try:
                    args_schema = self._build_args_schema(obj)

                    spec = ToolSpec(
                        name=tool_name,
                        description=obj.__doc__ or skill_meta["description"],
                        func=obj,
                        args_schema=args_schema
                    )

                    registry.register(spec, obj)

                    found_function = True
                    log.info("registered tool name=%s", tool_name)

                except Exception as e:
                    log.error("failed to register tool name=%s error=%s", tool_name, e)

            if not found_function:
                log.info("no allowed tools found file=%s", py_file.name)

    # -----------------------------
    # 加载 skills
    # -----------------------------
    def load(self):
        settings = get_settings()
        skill_cfg = settings.skills.configs

        log.info("loading local skills")
        discovered = self.discover()

        if not discovered:
            log.warning("no skills found")
            return

        for skill_file in discovered:
            skill_dir = skill_file.parent
            skill_name = skill_dir.name

            cfg = skill_cfg.get(skill_name, {})
            enabled = cfg.get("enabled", True)

            if not enabled:
                log.info("skipping disabled skill name=%s", skill_name)
                continue

            log.info("loading skill name=%s", skill_name)

            try:
                content = skill_file.read_text(encoding="utf-8")

                if not content.startswith("---"):
                    raise ValueError("SKILL.md missing frontmatter")

                parts = content.split("---", 2)
                meta = yaml.safe_load(parts[1])
                body = parts[2].strip()

                skill = {
                    "name": meta.get("name", skill_name),
                    "description": meta.get("description", ""),
                    "allowed-tools": meta.get("allowed-tools", []),
                    "content": body,
                    "path": str(skill_file)
                }

                self.skills.append(skill)
                log.info("loaded SKILL.md name=%s", skill["name"])

                # 加载 python tools
                self._load_python_tools(skill_dir, skill)

            except Exception as e:
                log.error("failed loading skill name=%s error=%s", skill_name, e)

        records = registry.list_records()
        log.info("skills loaded count=%s", len(self.skills))

        if not records:
            log.info("registered tools none")
        else:
            log.info(
                "registered tools count=%s tools=%s",
                len(records),
                [rec.spec.name for rec in records],
            )
