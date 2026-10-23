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
from .search import record_key


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


def final_evidence_view(cards, answer_cards, operations, limit, *, stop_reason=None):
    """Budget the complete final envelope before allocating individual previews.

    The manifest describes actual delivery independently of evidence truncation.
    Identifiers are either present in full or omitted with explicit pagination;
    large artifact bodies cannot silently remove a later delivered identity.
    """
    cards = list({card["result_id"]: card for card in cards}.values())
    answer_cards = list({card["result_id"]: card for card in answer_cards}.values())
    result = {"final_delivery": [], "answer_evidence": [], "delivery_manifest": [],
        "stop_reason": stop_reason}
    # Failure detail is explanatory text, never a source identifier.
    if len(encode(result))>limit:
        result["stop_reason"], _ = project(stop_reason, max(4, limit//8))
    if len(encode(result))>limit:
        return {}
    reserve = min(256, max(0, limit//4))
    for card in cards:
        entry = {"result_id": card["result_id"]}
        candidate = {**result, "delivery_manifest": [*result["delivery_manifest"], entry]}
        if len(encode(candidate))+reserve+96>limit:
            break
        result["delivery_manifest"].append(entry)
    if len(result["delivery_manifest"])<len(cards):
        result.update(delivery_total=len(cards), delivery_next_offset=len(result["delivery_manifest"]))
    # Names stay whole, just like IDs. A bounded manifest may omit a large
    # label; the corresponding evidence view can still expose it.
    for entry, card in zip(result["delivery_manifest"], cards):
        metadata = {key: card[key] for key in ("title", "view_type") if key in card}
        if len(encode(result))+len(encode(metadata))+4<=limit//3:
            entry.update(metadata)
    remaining = max(0, limit-len(encode(result))-128)
    displayed_budget = remaining*2//3 if answer_cards else remaining
    support_budget = remaining-displayed_budget if cards else remaining

    def add_group(key, source, budget):
        if not source:
            return
        group = evidence_group(source, operations, max(4, budget))
        result[key] = group.get("items", [])
        if len(result[key])<len(source):
            result[key+"_total"] = len(source)
            result[key+"_next_offset"] = len(result[key])

    add_group("final_delivery", cards, displayed_budget)
    add_group("answer_evidence", answer_cards, support_budget)
    # Group pagination metadata has a bounded but nonzero envelope cost.
    # Remove only entire previews if a deliberately tiny configured budget
    # cannot hold it; the manifest remains the authoritative delivery list.
    for key, source in (("answer_evidence", answer_cards), ("final_delivery", cards)):
        while result[key] and len(encode(result))>limit:
            result[key].pop()
            result[key+"_total"] = len(source)
            result[key+"_next_offset"] = len(result[key])
    if len(encode(result))>limit:
        minimal = {"delivery_manifest": result["delivery_manifest"]}
        if len(result["delivery_manifest"])<len(cards):
            minimal.update(delivery_total=len(cards), delivery_next_offset=len(result["delivery_manifest"]))
        return minimal if len(encode(minimal))<=limit else {}
    return result


def collection_paths(cards, operations):
    """Combine proven homogeneous artifacts; declarations may span targets.

    Old receipts retain their conservative surface-list rules. A runtime
    presentation descriptor can additionally prove an object surface and a
    shared family without using incidental field names as a type classifier.
    """
    origins, targets, paths, keys, families, kinds = set(), set(), {}, [], set(), set()
    declared = True
    if len({card.get("view_type") for card in cards})!=1:
        raise QAError("invalid_delivery", "不同展示类型不能合并为一个结果")
    for card in cards:
        receipts = [(item, attempt) for item in operations.items for attempt in item["attempts"]
            if attempt.get("result_id")==card["result_id"] and attempt["state"]=="succeeded"]
        if not receipts:
            raise QAError("invalid_delivery", "自动汇总缺少结果的执行来源")
        descriptors = []
        for item, attempt in receipts:
            tool = attempt.get("tool") or {}
            if not attempt.get("retry_safe") or not tool.get("server") or not tool.get("name"):
                raise QAError("invalid_delivery", "该工具未声明只读且幂等，请明确选择需要交付的产物")
            origins.add((tool["server"], tool["name"]))
            targets.add(encode(item.get("target")))
            descriptor = attempt.get("presentation")
            if descriptor is None:
                declared = False
            else:
                if (not isinstance(descriptor, dict) or not isinstance(descriptor.get("family"), str)
                        or not descriptor["family"] or descriptor.get("kind") not in {"object", "collection"}
                        or not isinstance(descriptor.get("path"), str)):
                    raise QAError("invalid_delivery", "结果的展示来源定义无效，不能自动合并")
                descriptors.append(descriptor)
                families.add(descriptor["family"])
                kinds.add(descriptor["kind"])
        if descriptors and (len(descriptors)!=len(receipts) or any(value!=descriptors[0] for value in descriptors[1:])):
            raise QAError("invalid_delivery", "结果的展示来源定义不一致，不能自动合并")
        if descriptors:
            descriptor = descriptors[0]
            try:
                value = at_path(card.get("data"), descriptor["path"])
            except QAError as exc:
                raise QAError("invalid_delivery", "返回内容不符合声明的展示结构，不能自动合并") from exc
            rows = [value] if descriptor["kind"]=="object" else value
            paths[card["result_id"]] = ({"path": descriptor["path"], "kind": descriptor["kind"],
                **({"identity": descriptor["identity"]} if descriptor.get("identity") else {})}
                if descriptor["kind"]=="object" or descriptor.get("identity") else descriptor["path"])
        else:
            surface = display_list(card)
            if surface is None:
                raise QAError("invalid_delivery", "结果不是可识别的同类对象列表，请选择直接满足目标的产物")
            rows = at_path(card.get("data"), surface["path"])
            paths[card["result_id"]] = surface["path"]
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise QAError("invalid_delivery", "自动汇总仅支持对象或对象列表，其他产物须明确选择")
        keys.extend(tuple(sorted(row)) for row in rows if row)
    if (len(origins)!=1 or (declared and (len(families)!=1 or len(kinds)!=1))
            or (not declared and (len(targets)!=1 or len(set(keys))>1
                or any(isinstance(path, dict) for path in paths.values())))):
        raise QAError("invalid_delivery", "结果的来源、目标或记录结构不兼容，不能自动合并")
    return paths


def combine_results(cards, path, result_id, title, lineage=None):
    """Project saved arrays/declared objects without inventing rows or totals."""
    rows, content, seen, media = [], [], set(), set()
    for card in cards:
        pointer = path[card["result_id"]] if isinstance(path, dict) else path
        identity = pointer.get("identity", []) if isinstance(pointer, dict) else []
        source_path = pointer.get("path", "") if isinstance(pointer, dict) else pointer
        if isinstance(pointer, dict) and pointer.get("kind") in {"object", "collection"} and isinstance(pointer.get("path"), str):
            value = at_path(card.get("data"), pointer["path"])
            if pointer["kind"]=="object":
                if not isinstance(value, dict):
                    raise QAError("invalid_delivery", "声明的对象位置必须指向完整对象")
                value = [value]
        else:
            value, _ = slice_result(card.get("data"), pointer, 0, len(encode(card)))
        if not isinstance(value, list):
            raise QAError("invalid_delivery", "合并位置必须指向数组")
        for index, row in enumerate(value):
            key = record_key(row, identity) if identity else fingerprint(row)
            if key not in seen:
                seen.add(key)
                rows.append(row)
                if lineage is not None:
                    lineage[str(len(rows)-1)] = {"result_id": card["result_id"], "path": source_path+(
                        "" if isinstance(pointer, dict) and pointer.get("kind")=="object" else "/"+str(index))}
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
