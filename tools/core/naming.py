# tools/naming.py
from __future__ import annotations

import re

# 选择一个“可逆且低冲突”的编码方式：
# internal: shell.exec
# external: shell__exec
_SEP = "__"

_VALID_EXTERNAL = re.compile(r"^[a-zA-Z0-9_]+$")


def qualify(namespace: str | None, tool_name: str) -> str:
    if not namespace:
        return tool_name
    if "." in tool_name:
        return tool_name
    return f"{namespace}.{tool_name}"


def to_external_name(internal_name: str) -> str:
    # 将 '.' 编码为 '__'，保证可逆
    external = internal_name.replace(".", _SEP)
    if not _VALID_EXTERNAL.match(external):
        # 最保守策略：把非法字符替换成 '_'（仍可逆性会弱化，但通常不会出现）
        external = re.sub(r"[^a-zA-Z0-9_]", "_", external)
    return external


def to_internal_name(external_name: str) -> str:
    # 将 '__' 解码回 '.'
    return external_name.replace(_SEP, ".")