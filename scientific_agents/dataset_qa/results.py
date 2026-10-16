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


def combine_results(cards, path, result_id, title):
    """Combine explicitly selected arrays without inventing rows or pagination totals."""
    rows, content, seen, media = [], [], set(), set()
    for card in cards:
        value, _ = slice_result(card.get("data"), path, 0, len(encode(card)))
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
    return {"result_id": result_id, "view_type": "tool_result", "title": title or "汇总结果",
        **ToolResult(rows, content).payload()}
