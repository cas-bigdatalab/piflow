import argparse
import re
from functools import lru_cache
from pathlib import Path

ELEMENTS = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
    "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm",
    "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
}
RARE_ELEMENTS = {
    "Ac", "Pa", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr",
    "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
}
SUBSCRIPT_MAP = str.maketrans({"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"})
SUPERSCRIPT_MAP = str.maketrans({"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁺": "+", "⁻": "-"})
SUBSCRIPT_CHARS = "₀₁₂₃₄₅₆₇₈₉"
SUPERSCRIPT_CHARS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻"
TOKEN_RE = re.compile(
    rf"(?<![A-Za-z0-9])(\d*)([A-Za-z][A-Za-z0-9()\[\]{SUBSCRIPT_CHARS}{SUPERSCRIPT_CHARS}]*)([+-]?)(?![A-Za-z0-9])"
)
BOND_RE = re.compile(r"(?<![A-Za-z])([A-Za-z]{1,6})([−–—‐≡⋮])([A-Za-z]{1,6})(?![A-Za-z])")
ARROW_RE = re.compile(r"→|⇒|⟶|⇌|↔|⇄|⇆")
ARROWS = {"→": "->", "⇒": "->", "⟶": "->", "⇌": "<->", "↔": "<->", "⇄": "<->", "⇆": "<->"}
BONDS = {"−": "-", "–": "-", "—": "-", "‐": "-", "≡": "#", "⋮": "#"}
INVISIBLE_RE = re.compile("[﻿​‌‍]")


def parse_standard_elements(letters: str) -> list[str] | None:
    symbols: list[str] = []
    index = 0
    while index < len(letters):
        if not letters[index].isupper():
            return None
        end = index + 1
        if end < len(letters) and letters[end].islower():
            end += 1
        symbol = letters[index:end]
        if symbol not in ELEMENTS:
            return None
        symbols.append(symbol)
        index = end
    return symbols


def parse_best_case_insensitive(letters: str) -> list[str] | None:
    lowered = letters.lower()

    @lru_cache(maxsize=None)
    def parse(index: int) -> tuple[int, tuple[str, ...]] | None:
        if index == len(lowered):
            return 0, ()
        best: tuple[int, tuple[str, ...]] | None = None
        for width in (1, 2):
            raw = lowered[index:index + width]
            if len(raw) != width:
                continue
            symbol = raw.capitalize()
            if symbol not in ELEMENTS:
                continue
            remainder = parse(index + width)
            if remainder is None:
                continue
            candidate = remainder[0] + 1 + (10 if symbol in RARE_ELEMENTS else 0), (symbol, *remainder[1])
            if best is None or candidate < best:
                best = candidate
        return best

    result = parse(0)
    return list(result[1]) if result is not None else None


def split_elements(letters: str) -> list[str] | None:
    standard = parse_standard_elements(letters)
    if standard is not None:
        return standard
    if letters.isupper() and all(character in ELEMENTS for character in letters):
        return list(letters)
    return parse_best_case_insensitive(letters)


def element_groups(token: str) -> list[list[str]] | None:
    groups = re.findall(r"[A-Za-z]+", token)
    if not groups:
        return None
    parsed = [split_elements(group) for group in groups]
    if any(symbols is None for symbols in parsed):
        return None
    return parsed


def letters_from_token(token: str) -> str:
    return "".join(character for character in token if character.isalpha())


def has_formula_marker(token: str) -> bool:
    return any(character.isdigit() or character in f"()[]{SUBSCRIPT_CHARS}{SUPERSCRIPT_CHARS}" for character in token)


def is_explicit_formula(token: str) -> bool:
    groups = element_groups(token)
    if groups is None:
        return False
    letters = letters_from_token(token)
    return has_formula_marker(token) or parse_standard_elements(letters) is not None or letters.isupper()


def reaction_line(line: str) -> bool:
    if not ARROW_RE.search(line):
        return False
    candidates = [match.group(2) for match in TOKEN_RE.finditer(line)]
    confident = [token for token in candidates if is_explicit_formula(token)]
    return len(confident) >= 2 and ("+" in line or any(has_formula_marker(token) for token in confident))


def is_reaction_operand(match: re.Match[str], line: str, is_reaction: bool) -> bool:
    if not is_reaction:
        return False
    before = line[:match.start()].rstrip()
    after = line[match.end():].lstrip()
    return (
        not before
        or before.endswith(("+", "→", "⇒", "⟶", "⇌", "↔", "⇄", "⇆"))
        or not after
        or after.startswith(("+", "→", "⇒", "⟶", "⇌", "↔", "⇄", "⇆"))
    )


def normalize_token(token: str, sign: str, reaction_context: bool) -> str:
    unicode_charge = ""
    superscript_match = re.search(rf"[{SUPERSCRIPT_CHARS}]+$", token)
    if superscript_match:
        unicode_charge = superscript_match.group(0).translate(SUPERSCRIPT_MAP)
        token = token[:superscript_match.start()]

    groups = element_groups(token)
    if groups is None:
        return token + (superscript_match.group(0) if superscript_match else "") + sign
    letters = letters_from_token(token)
    if not (has_formula_marker(token) or parse_standard_elements(letters) is not None or reaction_context):
        return token + (superscript_match.group(0) if superscript_match else "") + sign

    ascii_charge = ""
    if sign:
        trailing_digits = re.search(r"\d+$", token)
        if trailing_digits and sum(len(group) for group in groups) == 1 and "(" not in token and "[" not in token:
            ascii_charge = trailing_digits.group(0) + sign
            token = token[:trailing_digits.start()]
        else:
            ascii_charge = sign

    output: list[str] = []
    index = 0
    group_index = 0
    while index < len(token):
        character = token[index]
        if character.isalpha():
            while index < len(token) and token[index].isalpha():
                index += 1
            output.extend(groups[group_index])
            group_index += 1
        elif character in SUBSCRIPT_CHARS:
            end = index + 1
            while end < len(token) and token[end] in SUBSCRIPT_CHARS:
                end += 1
            output.append(f"_{{{token[index:end].translate(SUBSCRIPT_MAP)}}}")
            index = end
        elif character.isdigit():
            end = index + 1
            while end < len(token) and token[end].isdigit() and token[end] not in SUBSCRIPT_CHARS:
                end += 1
            output.append(f"_{{{token[index:end]}}}")
            index = end
        else:
            output.append(character)
            index += 1

    charge = unicode_charge or ascii_charge
    if charge:
        output.append(f"^{{{charge}}}")
    return "".join(output)


def normalize_bonds(line: str) -> str:
    def replace(match: re.Match[str]) -> str:
        left, bond, right = match.groups()
        if parse_standard_elements(left) is None or parse_standard_elements(right) is None:
            return match.group(0)
        return left + BONDS[bond] + right

    return BOND_RE.sub(replace, line)


def normalize_line(line: str) -> str:
    is_reaction = reaction_line(line)
    line = normalize_bonds(line)
    line = TOKEN_RE.sub(
        lambda match: match.group(1)
        + normalize_token(
            match.group(2),
            match.group(3),
            is_reaction_operand(match, line, is_reaction),
        ),
        line,
    )
    if is_reaction:
        line = ARROW_RE.sub(lambda match: ARROWS[match.group(0)], line)
    return line


def normalize_text(text: str) -> str:
    text = INVISIBLE_RE.sub("", text).replace(" ", " ")
    return "".join(normalize_line(line) for line in text.splitlines(keepends=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="规范化文本内的化学式、反应箭头、化学键与离子上下标")
    parser.add_argument("--input_path", required=True, help="包含化学表达式的 UTF-8 文本文件路径")
    parser.add_argument("--output_path", required=True, help="规范化文本文件的输出路径")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    content = input_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(normalize_text(content), encoding="utf-8")
    print(f"[OK] 化学表达式规范化完成 -> {output_path}")


if __name__ == "__main__":
    main()
