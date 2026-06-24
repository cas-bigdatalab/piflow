from agents.prompts import SKILL_CREATOR_PROMPT

SKILL_CREATOR_ROUTE_MARKER = "__ROUTE_TO_SKILL_CREATOR__"
SKILL_CREATOR_ROUTE_PROMPT_BLOCK = """
## skill生成路由规则
**如果对话需要生成json等特殊格式，忽略以下规则**

- 如果用户处理一了数据处理或清洗任务，始终应该在你认为用户指定的这次任务结束时询问用户是否生成对应skill，用户同意则输出标记。
- 如果上述场景没有命中skill内存在的功能时，优先输出这个标记。
- 命中上述场景时，只输出该标记：`__ROUTE_TO_SKILL_CREATOR__`
- 除这个标记外不要输出任何解释、前后缀、JSON、Markdown 或其它文字。
- 如果用户只是在询问总结功能、触发方式、工作原理，或表达仍然含糊，也继续按正常主流程响应，不要输出该标记。
""".strip()


def build_skill_creator_route_prompt_block() -> str:
    return SKILL_CREATOR_ROUTE_PROMPT_BLOCK


def is_skill_creator_route_marker(message: str | None) -> bool:
    if message is None:
        return False
    return str(message).strip() == SKILL_CREATOR_ROUTE_MARKER


def build_skill_creator_system_prompt() -> str:
    return SKILL_CREATOR_PROMPT.strip()
