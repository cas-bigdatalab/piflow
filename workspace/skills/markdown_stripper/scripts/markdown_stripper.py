import argparse
import re
import os
from typing import List


# ── 行内正则 ───────────────────────────────────────────────────────────
# 图片 ![alt](url) / ![alt][ref]
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
IMAGE_REF_RE = re.compile(r"!\[([^\]]*)\]\[[^\]]*\]")

# 链接 [text](url) / [text][ref]
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
LINK_REF_RE = re.compile(r"\[([^\]]+)\]\[[^\]]*\]")

# 行内代码 `code`
INLINE_CODE_RE = re.compile(r"(?<!`)`([^`]+)`(?!`)")

# 加粗 **text** / __text__
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
BOLD_ALT_RE = re.compile(r"__(.+?)__")

# 斜体 *text* / _text_（不匹配 ** 或 __）
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
ITALIC_ALT_RE = re.compile(r"(?<!_)_([^_\n]+)_(?!_)")

# 删除线 ~~text~~
STRIKETHROUGH_RE = re.compile(r"~~(.+?)~~")

# ── 行级正则 ───────────────────────────────────────────────────────────
HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
SETEXT_UNDERLINE_RE = re.compile(r"^(={3,}|-{3,})\s*$", re.MULTILINE)
BLOCKQUOTE_RE = re.compile(r"^>\s?", re.MULTILINE)
UNORDERED_LIST_RE = re.compile(r"^[\s]*[-*+]\s+", re.MULTILINE)
ORDERED_LIST_RE = re.compile(r"^[\s]*\d+\.\s+", re.MULTILINE)
HORIZONTAL_RULE_RE = re.compile(r"^[\s]*([-*_]\s*){3,}\s*$", re.MULTILINE)
REF_DEF_RE = re.compile(r"^\[[^\]]+\]:\s*\S+.*$", re.MULTILINE)

# ── 代码块 ─────────────────────────────────────────────────────────────
FENCED_CODE_RE = re.compile(r"```[\s\S]*?```")


def _strip_inline(text: str, keep_images: bool) -> str:
    s = text
    if keep_images:
        s = IMAGE_RE.sub(r"\1", s)
        s = IMAGE_REF_RE.sub(r"\1", s)
    else:
        s = IMAGE_RE.sub("", s)
        s = IMAGE_REF_RE.sub("", s)
    s = LINK_RE.sub(r"\1", s)
    s = LINK_REF_RE.sub(r"\1", s)
    s = BOLD_RE.sub(r"\1", s)
    s = BOLD_ALT_RE.sub(r"\1", s)
    s = ITALIC_RE.sub(r"\1", s)
    s = ITALIC_ALT_RE.sub(r"\1", s)
    s = STRIKETHROUGH_RE.sub(r"\1", s)
    s = INLINE_CODE_RE.sub(r"\1", s)
    return s


def _extract_fenced_code(text: str) -> tuple:
    codes = []
    PLACEHOLDER = "\x01CODEBLOCK_{}\x01"

    def _replace(m: re.Match) -> str:
        idx = len(codes)
        content = m.group(0)
        inner = content[3:-3].strip()
        if "\n" in inner:
            first_line, rest = inner.split("\n", 1)
            if first_line.strip() and not first_line.strip().startswith(" "):
                inner = rest
        codes.append(inner.strip())
        return PLACEHOLDER.format(idx)

    result = FENCED_CODE_RE.sub(_replace, text)
    return result, codes


def _restore_codes(text: str, codes: List[str]) -> str:
    for i, code in enumerate(codes):
        text = text.replace("\x01CODEBLOCK_{}\x01".format(i), code)
    return text


def _strip_lines(text: str) -> str:
    s = text
    s = REF_DEF_RE.sub("", s)
    s = HORIZONTAL_RULE_RE.sub("", s)
    s = SETEXT_UNDERLINE_RE.sub("", s)
    s = HEADING_RE.sub("", s)
    s = BLOCKQUOTE_RE.sub("", s)
    s = UNORDERED_LIST_RE.sub("", s)
    s = ORDERED_LIST_RE.sub("", s)
    return s


def _strip_table(text: str) -> str:
    lines = text.splitlines()
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            if re.match(r"^[\|\s\-:]+$", stripped):
                continue
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            result.append(" ".join(c for c in cells if c))
        else:
            result.append(line)
    return "\n".join(result)


def strip_markdown(
    text: str,
    keep_code_blocks: bool = True,
    keep_images: bool = True,
    keep_tables: bool = False,
) -> str:
    s = text
    s, codes = _extract_fenced_code(s)

    if not keep_tables:
        s = _strip_table(s)

    s = _strip_lines(s)
    s = _strip_inline(s, keep_images)

    if keep_code_blocks:
        s = _restore_codes(s, codes)
    else:
        for i in range(len(codes)):
            s = s.replace("\x01CODEBLOCK_{}\x01".format(i), "")

    s = re.sub(r"\n{3,}", "\n\n", s)
    s = s.strip()
    return s


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def main():
    parser = argparse.ArgumentParser(
        description="Markdown标记清除：去除标题、加粗、斜体、链接、代码块等Markdown语法标记，保留纯文本"
    )
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--no_code_blocks", type=str_to_bool, default=False, help="删除代码块内容（默认保留）")
    parser.add_argument("--no_images", type=str_to_bool, default=False, help="删除图片alt文本（默认保留）")
    parser.add_argument("--no_tables", type=str_to_bool, default=False, help="删除表格（默认转为纯文本）")

    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        raise FileNotFoundError(f"文件不存在: {args.input_path}")

    file_ext = os.path.splitext(args.input_path)[1].lower()
    if file_ext not in ('.md', '.txt', '.markdown'):
        raise ValueError(f"不支持的文件格式: {file_ext}。本skill仅支持 .md / .txt 文件")

    with open(args.input_path, "r", encoding="utf-8") as f:
        content = f.read()

    cleaned = strip_markdown(
        content,
        keep_code_blocks=not args.no_code_blocks,
        keep_images=not args.no_images,
        keep_tables=not args.no_tables,
    )

    output_dir = os.path.dirname(args.output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(args.output_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print(f"[OK] Markdown标记清除完成 -> {args.output_path}")
    print(f"   keep_code_blocks={not args.no_code_blocks}, keep_images={not args.no_images}, keep_tables={not args.no_tables}")


if __name__ == "__main__":
    main()
