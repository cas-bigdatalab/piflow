"""MCP output adapted to LangChain content blocks, separately from model evidence.

Uses the public langchain_core content builders, following LangChain's MCP
content/artifact separation: https://github.com/langchain-ai/langchain
No dependency on the newer, incompatible langchain.mcp integration.
"""
from dataclasses import dataclass, field
import json

from langchain_core.messages.content import (
    create_audio_block, create_file_block, create_image_block, create_text_block,
)

from .context import encode, project, public_result, slice_result
from .contracts import QAError
from .execution import fingerprint
from .references import at_path, display_list


def as_dict(value):
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    return vars(value)


def content_block(value):
    block = as_dict(value)
    kind = block.get("type")
    mime = block.get("mimeType", block.get("mime_type"))
    if kind == "text":
        return create_text_block(block["text"])
    if kind in {"image", "audio"}:
        builder = create_image_block if kind == "image" else create_audio_block
        return builder(base64=block["data"], mime_type=mime)
    if kind == "resource_link":
        builder = create_image_block if (mime or "").startswith("image/") else create_file_block
        return builder(url=str(block["uri"]), mime_type=mime,
            **({"name": block["name"]} if block.get("name") else {}))
    if kind == "resource":
        resource = as_dict(block["resource"])
        if "text" in resource:
            return create_text_block(resource["text"])
        mime = resource.get("mimeType", resource.get("mime_type"))
        if "blob" in resource:
            builder = create_image_block if (mime or "").startswith("image/") else create_file_block
            return builder(base64=resource["blob"], mime_type=mime)
    # Preserve future MCP block types for clients that understand them.
    return block


@dataclass
class ToolResult:
    data: object = None
    content: list = field(default_factory=list)

    @classmethod
    def from_mcp(cls, result, max_bytes):
        data = getattr(result, "structured_content", getattr(result, "structuredContent", None))
        blocks = [as_dict(b) for b in getattr(result, "content", [])]
        content = []
        for block in blocks:
            if block.get("type") == "text":
                try:
                    decoded = json.loads(block["text"])
                except (ValueError, TypeError):
                    decoded = block["text"]
                if data is not None and decoded == data:
                    continue  # MCP's text mirror is already present as structured data.
                if data is None and len(blocks) == 1:
                    data = decoded
                    continue
            converted = content_block(block)
            if converted is not block:
                converted.pop("id", None)  # Builders generate random optional IDs.
            content.append(converted)
        if data is None and not blocks:
            data = getattr(result, "data", None)
        output = cls(data, content)
        if len(encode(output.payload()).encode("utf-8")) > max_bytes:
            raise QAError("result_too_large", "工具返回内容超过运行预算", 502)
        return output

    def payload(self):
        value = {}
        if self.data is not None or not self.content:
            value["data"] = self.data
        if self.content:
            value["content"] = self.content
        return value


def evidence(card, limit):
    """A bounded model view. Binary data stays in the saved display artifact."""
    # Model evidence retains the saved structure so JSON Pointer reads stay valid.
    result = public_result(card, limit * 2 // 3 if card.get("content") else limit, normalize=False)
    if card.get("content"):
        blocks = []
        for block in card["content"]:
            if block.get("type") == "text":
                text, _ = project(block.get("text", ""), max(128, limit // 4))
                blocks.append({"type": "text", "text": text})
            else:
                blocks.append({k: block[k] for k in ("type", "mime_type", "name") if k in block})
        result["content"], cut = project(blocks, max(128, limit // 3))
        if cut:
            result["truncated"] = True
    return result


def evidence_group(cards, operations, limit):
    """One bounded, source-backed view; raw artifacts never enter session memory."""
    cards = list({card["result_id"]: card for card in cards}.values())
    owners = {}
    for operation in operations.items:
        for result_id in operations.result_ids(operation):
            owners.setdefault(result_id, []).append(operation["id"])
    result = {"items": [], "total": len(cards)}
    if len(encode({**result, "next_offset": 0}))>limit:
        return {}
    for card in cards:
        entry = {"result_id": card["result_id"], "operations": owners.get(card["result_id"], []), "truncated": True}
        # Keep identifiers whole, even when only a paged index fits.
        if len(encode({**result, "items": [*result["items"], entry], "next_offset": len(result["items"])+1}))+40>limit:
            break
        result["items"].append(entry)
    if len(result["items"])<len(cards):
        result["next_offset"] = len(result["items"])
    remaining = limit-len(encode(result))
    share = max(0, remaining//max(1, len(result["items"]))-24)
    for entry, card in zip(result["items"], cards):
        detail = {}
        if share>=64:
            view = evidence(card, share)
            detail, _ = project({key: value for key, value in view.items() if key!="result_id"}, share)
            entry.update(detail or {})
        entry["truncated"] = bool(card.get("truncated") or (detail or {}).get("truncated")) or "data" not in entry or entry.get("data")!=card.get("data")
    return result


def collection_paths(cards, operations):
    """Infer only compatible object lists backed by the same safe tool and target."""
    origins, targets, paths, keys = set(), set(), {}, []
    if len({card.get("view_type") for card in cards})!=1:
        raise QAError("invalid_delivery", "不同展示类型不能合并为一个结果")
    for card in cards:
        surface = display_list(card)
        if surface is None:
            raise QAError("invalid_delivery", "结果不是可识别的同类对象列表，请选择直接满足目标的产物")
        rows = at_path(card.get("data"), surface["path"])
        if any(not isinstance(row, dict) for row in rows):
            raise QAError("invalid_delivery", "自动汇总仅支持对象列表，其他产物须明确选择")
        keys.extend(tuple(sorted(row)) for row in rows if row)
        paths[card["result_id"]] = surface["path"]
        receipts = [(item, attempt) for item in operations.items for attempt in item["attempts"]
            if attempt.get("result_id")==card["result_id"] and attempt["state"]=="succeeded"]
        if not receipts:
            raise QAError("invalid_delivery", "自动汇总缺少结果的执行来源")
        for item, attempt in receipts:
            tool = attempt.get("tool") or {}
            if not attempt.get("retry_safe") or not tool.get("server") or not tool.get("name"):
                raise QAError("invalid_delivery", "该工具未声明只读且幂等，请明确选择需要交付的产物")
            origins.add((tool["server"], tool["name"]))
            targets.add(encode(item.get("target")))
    if len(origins)!=1 or len(targets)!=1 or len(set(keys))>1:
        raise QAError("invalid_delivery", "结果的来源、目标或记录结构不兼容，不能自动合并")
    return paths


def combine_results(cards, path, result_id, title):
    """Combine explicitly selected arrays without inventing rows or pagination totals."""
    rows, content, seen, media = [], [], set(), set()
    for card in cards:
        pointer = path[card["result_id"]] if isinstance(path, dict) else path
        value, _ = slice_result(card.get("data"), pointer, 0, len(encode(card)))
        if not isinstance(value, list):
            raise QAError("invalid_delivery", "合并位置必须指向数组")
        for row in value:
            key = fingerprint(row)
            if key not in seen:
                seen.add(key)
                rows.append(row)
        for block in card.get("content", []):
            key = fingerprint(block)
            if key not in media:
                media.add(key)
                content.append(block)
    view = cards[0].get("view_type", "tool_result") if cards else "tool_result"
    if not isinstance(view, str) or not view or any(card.get("view_type", "tool_result") != view for card in cards):
        view = "tool_result"
    return {"result_id": result_id, "view_type": view, "title": title or "汇总结果",
        **ToolResult(rows, content).payload()}
