from agents.prompts import SKILL_CREATOR_PROMPT

SKILL_CREATOR_ROUTE_MARKER = "__ROUTE_TO_SKILL_CREATOR__"
SKILL_CREATOR_ROUTE_PROMPT_BLOCK = """
## skill生成路由规则
- 只有在“已经获得用户许可进入 skill 生成路径”时，才输出路由标记：`__ROUTE_TO_SKILL_CREATOR__`
- **必须在消息开头直接输出路由标记**，即消息以 `__ROUTE_TO_SKILL_CREATOR__` 开头；禁止在标记前附带任何解释、前缀、空格或其它文字。
- 输出路由标记时，只输出该标记本身；不要输出任何解释、前后缀、JSON、Markdown 或其它文字。
- 当用户当前请求本身就是生成、保存、封装、补齐、创建或沉淀 skill 时，可直接输出路由标记。
- 如果是在 DAG 规划、工作流规划或节点编排过程中发现关键 skill 缺失，且继续规划会导致 DAG 无法合法闭环，不要直接输出路由标记。
- 此时先正常回复用户，说明当前缺少完成 DAG 所需的关键 skill，现有技能库无法覆盖，并询问是否允许转入 skill 生成路径；只有在用户明确同意后，才输出路由标记。
- 如果用户只是在询问总结功能、触发方式、工作原理，或表达仍然含糊、尚不足以判断是否需要 skill 生成，则继续按正常主流程响应，不要输出路由标记。
""".strip()

# 从文本中剥离路由标记的工具函数
STRIP_MARKER_PATTERNS = [SKILL_CREATOR_ROUTE_MARKER]


def strip_route_marker(text: str) -> str:
    """从文本中移除所有路由标记，防止泄露给用户。"""
    result = text
    for pattern in STRIP_MARKER_PATTERNS:
        result = result.replace(pattern, "")
    return result.strip()


def build_skill_creator_route_prompt_block() -> str:
    return SKILL_CREATOR_ROUTE_PROMPT_BLOCK


def is_skill_creator_route_marker(message: str | None) -> bool:
    if message is None:
        return False
    # 使用 in 而非 ==，以兼容文本中混入标记的情况
    return SKILL_CREATOR_ROUTE_MARKER in str(message)


def build_skill_creator_system_prompt() -> str:
    return SKILL_CREATOR_PROMPT.strip()
