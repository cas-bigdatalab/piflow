#!/usr/bin/env python3
"""Normalize the display syntax of basic mathematical expressions in UTF-8 text."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


INVISIBLE_CHARACTERS = "﻿​‌‍⁠"
UNICODE_OPERATOR_MAP = str.maketrans(
    {
        "−": "-", "–": "-", "＋": "+", "±": "+-", "×": "*", "·": "*",
        "∙": "*", "⋅": "*", "÷": "/", "／": "/", "＝": "=", "≤": "<=",
        "≥": ">=", "≠": "!=", "≈": "~", "∗": "*", "∕": "/",
        "→": "->", "⇒": "->", "⟶": "->", "↔": "<->", "⇌": "<->",
    }
)
UNICODE_BRACKET_MAP = str.maketrans(
    {
        "（": "(", "）": ")", "﹙": "(", "﹚": ")", "｟": "(", "｠": ")",
        "［": "[", "］": "]", "【": "[", "】": "]", "〔": "[", "〕": "]",
        "｛": "{", "｝": "}", "﹛": "{", "﹜": "}",
    }
)
SUPERSCRIPTS = str.maketrans(
    {
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
        "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁺": "+", "⁻": "-",
        "⁼": "=", "⁽": "(", "⁾": ")", "ⁿ": "n", "ⁱ": "i",
    }
)
SUBSCRIPTS = str.maketrans(
    {
        "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5",
        "₆": "6", "₇": "7", "₈": "8", "₉": "9", "₊": "+", "₋": "-",
        "₌": "=", "₍": "(", "₎": ")", "ₐ": "a", "ₑ": "e", "ₕ": "h",
        "ᵢ": "i", "ⱼ": "j", "ₖ": "k", "ₗ": "l", "ₘ": "m", "ₙ": "n",
        "ₒ": "o", "ₚ": "p", "ᵣ": "r", "ₛ": "s", "ₜ": "t", "ᵤ": "u",
        "ᵥ": "v", "ₓ": "x",
    }
)
SUPERSCRIPT_CHARS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ"
SUBSCRIPT_CHARS = "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"
SUPERSCRIPT_RUN = re.compile(f"[{SUPERSCRIPT_CHARS}]+")
SUBSCRIPT_RUN = re.compile(f"[{SUBSCRIPT_CHARS}]+")
VARIABLE = rf"[A-Za-zΑ-Ωα-ω](?:[{SUPERSCRIPT_CHARS}{SUBSCRIPT_CHARS}]+)?"
NUMBER = rf"[+\-−＋]?\d+(?:\.\d+)?(?:[{SUPERSCRIPT_CHARS}{SUBSCRIPT_CHARS}]+)?"
BRACKET = r"[()\[\]{}（）﹙﹚｟｠［］【】〔〕｛｝﹛﹜]"
ATOM = rf"(?:{VARIABLE}|{NUMBER}|{BRACKET})"
OPERATOR = r"(?:<->|->|!=|<=|>=|[+*/=<>~\-−–＋±×·∙⋅÷／＝≤≥≠≈∗∕→⇒⟶↔⇌])"
HSPACE = r"[^\S\r\n]"
FORMULA_SPAN = re.compile(
    rf"(?:(?<![A-Za-zΑ-Ωα-ω])(?:{VARIABLE}|{NUMBER})|{BRACKET})"
    rf"(?:{HSPACE}+{ATOM})*{HSPACE}*{OPERATOR}{HSPACE}*{ATOM}"
    rf"(?:(?:{HSPACE}+{ATOM})|(?:{HSPACE}*{OPERATOR}{HSPACE}*{ATOM}))*(?![A-Za-zΑ-Ωα-ω])"
)
FORMULA_CONTEXT = re.compile(
    rf"(?:!=|<=|>=|<->|->|[+*/=<>~^_−＋×÷＝≤≥≠≈±·∙⋅∕∗／→⇒⟶↔⇌{SUPERSCRIPT_CHARS}{SUBSCRIPT_CHARS}])"
)
ENGLISH_ENUMERATION = re.compile(r"\b[A-Z]\s+[\-–]\s+(?:I|you|we|they|he|she|it)\b")
STANDALONE_SCRIPT = re.compile(
    "(?P<base>[A-Za-zΑ-Ωα-ω0-9)\\]}])"
    f"(?P<script>[{SUPERSCRIPT_CHARS}{SUBSCRIPT_CHARS}]+)"
)
SPACE_AROUND_OPERATORS = re.compile(r"\s*(?:(!=|<=|>=|<->|->)|([+*/=<>~\-]))\s*")
SPACE_INSIDE_BRACKETS = re.compile(r"([([{])\s+|\s+([)\]}])")
ADJACENT_FORMULA_ATOMS = re.compile(
    r"(?<=[A-Za-zΑ-Ωα-ω0-9)\]}])\s+(?=[A-Za-zΑ-Ωα-ω0-9([{])"
)


def _convert_runs(text: str) -> str:
    text = SUPERSCRIPT_RUN.sub(
        lambda match: "^{" + match.group().translate(SUPERSCRIPTS) + "}", text
    )
    return SUBSCRIPT_RUN.sub(
        lambda match: "_{" + match.group().translate(SUBSCRIPTS) + "}", text
    )


def _normalize_formula_span(match: re.Match[str]) -> str:
    text = match.group(0).translate(UNICODE_BRACKET_MAP).translate(UNICODE_OPERATOR_MAP)
    text = _convert_runs(text)
    text = SPACE_AROUND_OPERATORS.sub(lambda item: item.group(1) or item.group(2), text)
    text = SPACE_INSIDE_BRACKETS.sub(lambda item: item.group(1) or item.group(2), text)
    return ADJACENT_FORMULA_ATOMS.sub("", text)


def _normalize_standalone_script(match: re.Match[str]) -> str:
    return match.group("base") + _convert_runs(match.group("script"))


def normalize_formula_text(text: str) -> str:
    text = text.translate(str.maketrans({character: None for character in INVISIBLE_CHARACTERS}))
    text = text.replace(" ", " ")
    protected: list[str] = []

    def protect_enumeration(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"{len(protected) - 1}"

    text = ENGLISH_ENUMERATION.sub(protect_enumeration, text)
    text = FORMULA_SPAN.sub(_normalize_formula_span, text)
    lines = []
    for line in text.splitlines(keepends=True):
        if FORMULA_CONTEXT.search(line):
            line = line.translate(UNICODE_BRACKET_MAP)
        lines.append(line)
    text = "".join(lines)
    text = STANDALONE_SCRIPT.sub(_normalize_standalone_script, text)
    for index, value in enumerate(protected):
        text = text.replace(f"{index}", value)
    return text


def normalize_file(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(normalize_formula_text(source), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="规整 UTF-8 文本内嵌数理公式的上下标、符号和括号格式。")
    parser.add_argument("--input_path", required=True, help="包含数理公式的 UTF-8 文本文件路径")
    parser.add_argument("--output_path", required=True, help="规整后文本文件的输出路径")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    normalize_file(Path(args.input_path), Path(args.output_path))
    print(f"[OK] 科学公式格式规整完成 -> {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
