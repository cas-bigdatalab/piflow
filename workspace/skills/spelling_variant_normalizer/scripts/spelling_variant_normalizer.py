import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# ── 英→美拼写词典 ──────────────────────────────────────────────────────
BRITISH_TO_AMERICAN: Dict[str, str] = {
    # -our → -or
    "colour": "color", "flavour": "flavor", "honour": "honor",
    "humour": "humor", "labour": "labor", "neighbour": "neighbor",
    "rumour": "rumor", "savour": "savor", "behaviour": "behavior",
    "favourite": "favorite", "harbour": "harbor", "odour": "odor",
    "parlour": "parlor", "splendour": "splendor", "vigour": "vigor",
    "armour": "armor", "candour": "candor", "clamour": "clamor",
    "endeavour": "endeavor", "glamour": "glamor", "rancour": "rancor",
    "rigour": "rigor", "valour": "valor", "vapour": "vapor",

    # -re → -er
    "centre": "center", "fibre": "fiber", "litre": "liter",
    "metre": "meter", "theatre": "theater", "calibre": "caliber",
    "lustre": "luster", "meagre": "meager", "sabre": "saber",
    "sceptre": "scepter", "sombre": "somber", "spectre": "specter",

    # -ise → -ize
    "organise": "organize", "recognise": "recognize", "realise": "realize",
    "apologise": "apologize", "authorise": "authorize",
    "organisation": "organization", "organisations": "organizations",
    "characterise": "characterize", "civilise": "civilize",
    "emphasise": "emphasize", "initialise": "initialize",
    "optimise": "optimize", "summarise": "summarize",
    "utilise": "utilize", "visualise": "visualize",
    # 屈折形式
    "organises": "organizes", "organised": "organized", "organising": "organizing",
    "recognises": "recognizes", "recognised": "recognized", "recognising": "recognizing",
    "realises": "realizes", "realised": "realized", "realising": "realizing",
    "apologises": "apologizes", "apologised": "apologized",
    "authorises": "authorizes", "authorised": "authorized",
    "characterises": "characterizes", "characterised": "characterized",
    "emphasises": "emphasizes", "emphasised": "emphasized",
    "initialises": "initializes", "initialised": "initialized",
    "optimises": "optimizes", "optimised": "optimized",
    "summarises": "summarizes", "summarised": "summarized",
    "utilises": "utilizes", "utilised": "utilized",
    "visualises": "visualizes", "visualised": "visualized",

    # -yse → -yze
    "analyse": "analyze", "paralyse": "paralyze", "catalyse": "catalyze",
    # 屈折形式
    "analyses": "analyzes", "analysed": "analyzed", "analysing": "analyzing",
    "paralyses": "paralyzes", "paralysed": "paralyzed",

    # -our → -or (复数/屈折)
    "colours": "colors", "coloured": "colored", "colouring": "coloring",
    "flavours": "flavors", "flavoured": "flavored", "favoured": "favored",
    "honours": "honors", "honoured": "honored",
    "humours": "humors", "labours": "labors",
    "neighbours": "neighbors", "neighbouring": "neighboring",
    "rumours": "rumors", "behaviours": "behaviors",
    "favourites": "favorites", "endeavours": "endeavors",

    # -ce → -se (复数)
    "defences": "defenses", "offences": "offenses",
    "licences": "licenses",

    # -ogue → -og (复数)
    "catalogue": "catalog", "catalogues": "catalogs", "dialogue": "dialog", "dialogues": "dialogs",

    # double L → single L
    "travelling": "traveling", "travelled": "traveled", "traveller": "traveler",
    "labelling": "labeling", "labelled": "labeled", "counselling": "counseling",
    "counsellor": "counselor", "marvellous": "marvelous", "modelling": "modeling",
    "quarrelling": "quarreling", "signalling": "signaling", "totalling": "totaling",
    "woollen": "woolen",

    # -mme → -m
    "programme": "program", "kilogramme": "kilogram",

    # -ae/-oe → -e
    "encyclopaedia": "encyclopedia", "foetus": "fetus", "anaemia": "anemia",
    "anaesthesia": "anesthesia", "diarrhoea": "diarrhea", "gynaecology": "gynecology",
    "haemoglobin": "hemoglobin", "leukaemia": "leukemia", "oedema": "edema",
    "oesophagus": "esophagus", "orthopaedic": "orthopedic", "paediatric": "pediatric",

    # misc
    "ageing": "aging", "aluminium": "aluminum", "axe": "ax",
    "cheque": "check", "cosy": "cozy", "draught": "draft",
    "grey": "gray", "jewellery": "jewelry", "judgement": "judgment",
    "kerb": "curb", "manoeuvre": "maneuver", "mould": "mold",
    "moustache": "mustache", "plough": "plow", "pyjamas": "pajamas",
    "sceptic": "skeptic", "smoulder": "smolder", "speciality": "specialty",
    "storey": "story", "sulphur": "sulfur", "tyre": "tire",
    "vice": "vise",
}


def _load_custom_dict(path: str) -> Dict[str, str]:
    """从 JSON/CSV/TSV 加载自定义词典"""
    ext = Path(path).suffix.lower()
    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif ext in (".csv", ".tsv"):
        sep = "\t" if ext == ".tsv" else ","
        df = pd.read_csv(path, sep=sep, encoding="utf-8")
        # 取前两列
        return dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))
    else:
        raise ValueError(f"不支持的自定义词典格式: {ext}")


def _build_replacement_map(
    brit_to_am: Dict[str, str],
    direction: str,
) -> List[Tuple[re.Pattern, str]]:
    """构建 (正则, 替换文本) 列表，支持大小写保持"""
    pairs = []
    for brit, am in brit_to_am.items():
        src = brit if direction == "british_to_american" else am
        dst = am if direction == "british_to_american" else brit
        if src == dst:
            continue

        # 构建保留大小写的替换函数
        def _repl(m: re.Match, src_w=src, dst_w=dst) -> str:
            word = m.group(0)
            # 全大写 → 目标全大写
            if word.isupper():
                return dst_w.upper()
            # 首字母大写 → 目标首字母大写
            if word[0].isupper():
                return dst_w.capitalize()
            return dst_w

        pat = re.compile(rf"\b{re.escape(src)}\b", re.IGNORECASE)
        pairs.append((pat, _repl))

    return pairs


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _normalize_text(text: str, pairs: List[Tuple[re.Pattern, callable]]) -> str:
    s = text
    for pat, repl in pairs:
        s = pat.sub(repl, s)
    return s


def normalize_spelling(
    df: pd.DataFrame,
    cols: List[str],
    pairs: List[Tuple[re.Pattern, callable]],
) -> pd.DataFrame:
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: _normalize_text(str(x), pairs) if not pd.isna(x) else x
        )
    return result


def run_normalizer(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    direction: str,
    custom_dict: Optional[str],
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        cols = _select_columns(df, None)

    # 构建词典
    brit_to_am = dict(BRITISH_TO_AMERICAN)
    if custom_dict:
        extra = _load_custom_dict(custom_dict)
        brit_to_am.update(extra)
        print(f"[INFO] 加载自定义词典: {custom_dict} ({len(extra)} 条)")

    pairs = _build_replacement_map(brit_to_am, direction)
    total_pairs = len(pairs)

    cleaned = normalize_spelling(df, cols=cols, pairs=pairs)
    write_structured_data(cleaned, output_path)
    print(
        f"[OK] 拼写变体规范化完成 -> {output_path}\n"
        f"   文本列: {cols}\n"
        f"   方向: {direction}, 词条数: {total_pairs}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="拼写变体标准化：统一英美拼写差异（colour→color、analyse→analyze 等）"
    )
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument(
        "--text_columns",
        required=False,
        default=None,
        help="处理的文本列，逗号分隔；默认全部字符串列",
    )
    parser.add_argument(
        "--direction",
        required=False,
        default="british_to_american",
        choices=["british_to_american", "american_to_british"],
        help="转换方向（默认 british_to_american）",
    )
    parser.add_argument(
        "--custom_dict",
        required=False,
        default=None,
        help="自定义词典文件路径（JSON/CSV/TSV）",
    )
    args = parser.parse_args()
    run_normalizer(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        direction=args.direction,
        custom_dict=args.custom_dict,
    )


if __name__ == "__main__":
    main()
