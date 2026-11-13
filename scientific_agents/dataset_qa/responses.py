"""User-facing outcomes, separated from private execution diagnostics.

Closing a conversation turn does not assert that its data operations succeeded.
The persisted receipts remain authoritative for retries, recovery and delivery.
No exception message or detail is copied into a public response.
"""
import html
import re
from urllib.parse import urlsplit


def delivery_links(cards):
    """Bounded, source-backed links shared by answer guidance and rendering.

    The caller supplies only selected delivery cards. Names and file facts come
    from the same object as the URL; wrappers are not evidence of file identity.
    """
    nodes_left, links = 2000, {}
    wrappers = ("data", "items", "result", "results", "files", "links")
    fields = {"downloadurl": "下载", "downloadurls": "下载",
              "previewurl": "查看", "previewurls": "查看"}

    def add(url, label, action, owner, facts):
        nonlocal nodes_left
        if nodes_left<=0:
            return False
        nodes_left -= 1
        if not isinstance(url, str) or not url or len(url)>8192:
            return False
        try:
            parsed = urlsplit(url)
            if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                    or parsed.username is not None or parsed.password is not None or parsed.port == 0
                    or any(c.isspace() or ord(c)<32 or ord(c)==127 or c in '\\<>"`' for c in url)):
                return False
        except ValueError:
            return False
        entry = {"result_id": owner.get("result_id"), "url": url, "label": label,
                 "action": action, "_title": owner.get("title", "")}
        if isinstance(facts.get("format"), str) and facts["format"]:
            entry["format"] = facts["format"][:64]
        if type(facts.get("record_count")) is int and facts["record_count"]>=0:
            entry["record_count"] = facts["record_count"]
        links.setdefault(url, entry)
        return True

    def walk(value, label, owner, *, url_view=False, depth=0):
        nonlocal nodes_left
        if nodes_left<=0 or depth>8:
            return
        nodes_left -= 1
        if isinstance(value, str):
            if url_view:
                add(value, label, "查看", owner, {})
        elif isinstance(value, list):
            for child in value:
                if nodes_left<=0:
                    break
                walk(child, label, owner, url_view=url_view, depth=depth+1)
        elif isinstance(value, dict):
            names = [value.get(key) for key in ("fileName", "filename", "name", "title")]
            label = next((name for name in names if isinstance(name, str) and name.strip()), label)
            # The resource's own name wins when a wrapper repeats its URL.
            # A different wrapper URL must never borrow that resource's name.
            if "resource" in value:
                walk(value["resource"], label, owner, url_view=url_view, depth=depth+1)
            found = False
            for key, child in value.items():
                key = str(key).replace("_", "").lower()
                action = fields.get(key) or ("查看" if url_view and key in {"url", "uri", "href"} else None)
                if action:
                    for url in child[:2000] if isinstance(child, list) else (child,):
                        found = add(url, label, action, owner, value) or found
            for key in wrappers:
                # A result's data rows are not additional delivery links.
                if key in value and not (found and key in {"data", "items", "result", "results"}):
                    walk(value[key], label, owner, url_view=url_view or key=="links", depth=depth+1)

    for card in cards:
        label = card.get("title") if isinstance(card.get("title"), str) and card["title"] else "结果"
        walk(card.get("data"), label, card, url_view=card.get("view_type")=="url")
        for block in card.get("content", []):
            if isinstance(block, dict) and block.get("type") in {"file", "resource_link"}:
                walk(block, label, card, url_view=True)

    values = list(links.values())
    groups = {}
    for entry in values:
        entry["label"] = " ".join(entry["label"].split())[:160]
        groups.setdefault(entry["label"], []).append(entry)
    for index, entry in enumerate(values, 1):
        group = groups[entry["label"]]
        if len(group)>1:
            titles = [item["_title"] for item in group]
            prefix = entry["_title"] if all(titles) and len(set(titles))==len(titles) else f"结果 {index}"
            entry["label"] = prefix+" · "+entry["label"]
    for entry in values:
        entry.pop("_title")
    return values


def _reply_link_view(message):
    """Ignore code examples; retain an open block fence for append-only repair."""
    visible, fence = [], None
    for line in message.splitlines():
        marker = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0]==fence[0] and len(marker[1])>=len(fence) and not marker[2].strip():
                fence = None
        elif marker and (marker[1][0]=="~" or "`" not in marker[2]):
            fence = marker[1]
        elif not line.startswith(("    ", "\t")):
            visible.append(line)
    text = "\n".join(visible)
    text = re.sub(r"(?<!`)(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)", "", text)
    return html.unescape(text), fence


def _has_complete_link(text, url):
    # Match against the exact authoritative URL, not a prefix of a signed URL.
    # This intentionally recognizes only common link forms, not arbitrary HTML.
    target = "".join((r"\\?" if character in r"\`*_{}[]()#+.!>-" else "")+re.escape(character)
                     for character in url)
    label = r"(?<!!)\[(?:\\.|[^\]\\\n])*\]"
    destination = r"(?:<"+target+r">|"+target+r")"
    if re.search(label+r"\(\s*"+destination+r"(?:[ \t]+[\"'][^\n]*?[\"'])?\s*\)", text):
        return True
    for match in re.finditer(target, text):
        before, after = text[:match.start()], text[match.end():]
        # A complete URL inside an unfinished Markdown target is still not a
        # complete link. The separately appended link must remain available.
        if re.search(r"\]\s*\([^)]*$", before.rsplit("\n\n", 1)[-1]):
            continue
        if before.endswith("<") and after.startswith(">"):
            return True
        previous = before[-1:]
        if previous and not (previous.isspace() or previous in ":：，。；（(" or "\u4e00"<=previous<="\u9fff"):
            continue
        if re.match(r'^(?:$|[\s<>"`\)\]，。；！？]|[.,;!?](?:\s|$))', after):
            return True
    return False


def delivery_link_suffix(message, cards):
    """Append missing delivery links without model or network calls."""
    rendered, fence = _reply_link_view(message)
    lines, size, omitted = [], 0, False
    for entry in delivery_links(cards):
        url, label, action = entry["url"], entry["label"], entry["action"]
        if _has_complete_link(rendered, url):
            continue
        label = re.sub(r"([\\`*_{}\[\]#!|])", r"\\\1", html.escape(label))
        # Angle-bracket destinations preserve parentheses and signed query
        # strings. Entity escaping does not change the browser's destination.
        line = f"- [{action}：{label}](<{html.escape(url, quote=False)}>)"
        if len(lines)>=20 or size+len(line)>12000:
            omitted = True
            continue
        lines.append(line)
        size += len(line)+1
    if not lines:
        return ""
    if omitted:
        lines.append("更多链接请查看下方结果。")
    return ("\n"+fence if fence else "")+("\n\n" if message else "")+"结果链接：\n\n"+"\n".join(lines)


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
    from .contracts import QAError
    from .references import at_path
    from .search import record_key

    by_id = {card["result_id"]: card for card in cards}
    sections = []
    for item in operations.deliverable(partial=True):
        if operations.required and not item.get("required", True):
            continue
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
    if code == "artifact_unavailable":
        return ("已取得的结果仍保留。" if retained else "")+"本次结果文件尚未准备好，当前还不能提供下载。您可以稍后让我继续获取或导出。"
    if retained:
        return "已取得的部分结果已保留在下方，您可以先查看。其余内容目前还没有可确认的结果；您可以指定下一步要查看或处理的内容。"
    detail = error.get("detail") if isinstance(error, dict) else getattr(error, "detail", None)
    if code == "task_timeout" and detail == {"phase": "queue"}:
        return "本轮尚未开始处理您的请求。您可以稍后让我继续，我会按原来的要求获取内容。"
    if code in {"execution_unknown", "task_timeout"}:
        return "这次还没有收到可确认的完整结果。为避免重复处理，可能已经执行的操作需要先确认结果。您也可以指定其他要查看的内容。"
    if code in {"invalid_parameters", "invalid_pointer", "result_not_found", "invalid_tool_call"}:
        return "本次尚未取得可确认的完整结果。您已提供的要求仍保留，可以稍后让我按原要求继续处理。"
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
