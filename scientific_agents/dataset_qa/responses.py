"""User-facing outcomes, separated from private execution diagnostics.

Closing a conversation turn does not assert that its data operations succeeded.
The persisted receipts remain authoritative for retries, recovery and delivery.
No exception message or detail is copied into a public response.
"""


def _code(error):
    if isinstance(error, dict):
        return error.get("error_code", error.get("code"))
    return getattr(error, "code", None)


def recovery_search_summary(operations, cards):
    """Render saved search facts locally when further execution cannot proceed.

    Read only successful receipts and their declared collection paths. This
    neither executes a tool nor turns intermediate findings into goal success.
    Error diagnostics and planner-authored recovery text are never inputs.
    """
    import html
    import re

    from .contracts import QAError
    from .references import at_path
    from .search import record_key

    by_id = {card["result_id"]: card for card in cards}
    sections = []
    for item in operations.deliverable(partial=True):
        search = item.get("search")
        if not search:
            continue
        rows = {}
        for attempt in item["attempts"]:
            card = by_id.get(attempt.get("result_id"))
            presentation = attempt.get("presentation") or {}
            if attempt["state"]!="succeeded" or card is None or presentation.get("kind")!="collection":
                continue
            try:
                values = at_path(card.get("data"), presentation["path"])
            except QAError:
                continue
            if isinstance(values, list):
                for row in values:
                    if isinstance(row, dict):
                        rows.setdefault(record_key(row, search["profile"].get("identity", [])), row)
        if rows:
            lines = [f"在本次检索范围内已取得 {len(rows)} 个候选数据集："]
            for row in list(rows.values())[:6]:
                title = row.get("title")
                if isinstance(title, str) and title.strip() and len(title)<=240:
                    label = re.sub(r"([\\`*_{}\[\]#!|])", r"\\\1", html.escape(" ".join(title.split())))
                else:
                    label = "名称请见下方结果" if title else "名称未提供，请查看下方记录"
                lines.append("- "+label)
            if len(rows)>6:
                lines.append("其余候选请查看下方结果。")
            lines.append("以上为检索候选，具体内容是否适用还需核实；您可以继续指定要查看或处理的内容。")
            sections.append("\n\n".join((lines[0], "\n".join(lines[1:-1]), lines[-1])))
        elif search["done"] and search.get("stop")=="exhausted" and not search["records"]:
            sections.append("本次检索范围内暂未找到匹配的数据集。您可以补充其他名称线索或指定其他检索范围。")
    return "\n\n".join(sections)


def notice(error, retained=False, subject=None):
    code = _code(error)
    if retained:
        return "已取得的结果已保留在下方，您可以先查看。其余内容目前还没有可确认的结果；您可以指定下一步要查看或处理的内容。"
    detail = error.get("detail") if isinstance(error, dict) else getattr(error, "detail", None)
    if code == "task_timeout" and detail == {"phase": "queue"}:
        return "本轮尚未开始处理您的请求。您可以稍后让我继续，我会按原来的要求获取内容。"
    if code in {"execution_unknown", "task_timeout"}:
        return "这次还没有收到可确认的完整结果。为避免重复处理，可能已经执行的操作需要先确认结果。您也可以指定其他要查看的内容。"
    if code in {"invalid_parameters", "invalid_pointer", "result_not_found", "invalid_tool_call"}:
        return "这次还需要确认操作对象或具体要求。您可以告诉我要查看的数据集名称，或指定希望获取的内容，我会据此继续处理。"
    if code in {"result_too_large", "context_too_large", "step_limit", "no_progress", "invalid_delivery"}:
        return "目前的信息还不足以给出完整结果。您可以指定优先查看的数据集或缩小范围，我会围绕这部分继续整理。"
    if code == "tool_failed":
        # An opaque tool rejection proves no usable output, not a temporary
        # outage, permanent lack of support, or a problem with search scope.
        return (f"本次没有取得可展示的{subject}。" if subject else "本次没有取得可展示的内容。")+"您可以选择其他数据集，或指定其他希望了解的信息。"
    return "本次没有取得可展示的内容。您可以指定其他希望查看或处理的信息。"


def terminal_reply(status, error=None, retained=False):
    if status == "CANCELLED":
        return ("已停止继续处理，已取得的结果保留在下方。您可以随时告诉我下一步要做什么。" if retained else
                "已停止继续处理。您可以随时告诉我下一步要做什么。")
    if status == "COMPLETED":
        return "结果已整理在下方，您可以继续指定要查看或处理的内容。" if retained else "您可以继续说明要查看的数据集或希望获取的内容，我会据此继续协助。"
    return notice(error, retained)


def public_completion(value, payload):
    """Project a handled turn without mislabelling private operations as success."""
    result = dict(value)
    if result.get("status") == "FAILED":
        evidence = bool(payload.get("delivery")) or any(
            attempt.get("state") == "succeeded" and attempt.get("result_id")
            for item in payload.get("operations", []) for attempt in item.get("attempts", []))
        result.update(status="COMPLETED", outcome="partial" if evidence else "unavailable",
                      message=notice(payload.get("error"), bool(payload.get("delivery"))))
    # Old persisted terminal events may contain an upstream error verbatim.
    for key in ("code", "error_code", "error_message", "detail"):
        result.pop(key, None)
    return result


def response_labels(operations, labels):
    """Labels authored after seeing diagnostics are private planning text."""
    from .operations import Operations

    result = Operations(operations.items)
    if labels is not None:
        for item in result.items:
            if labels.get(item["id"]) != item["description"]:
                # Prefer the original intent, then an adapter-authored business
                # name. Omit an unknown label instead of inventing a task number.
                item["description"] = labels.get(item["id"]) or item.get("public_label") or ""
    return result


def response_operations(operations, labels=None):
    """Only outcome facts reach the answer writer; diagnostics stay in planning."""
    value = response_labels(operations, labels).view()
    for item in value["items"]:
        item.pop("error", None)
        item.pop("capability", None)
    return value
