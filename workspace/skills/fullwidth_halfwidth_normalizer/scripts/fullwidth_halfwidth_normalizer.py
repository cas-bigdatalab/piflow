import argparse
import sys
import unicodedata
from pathlib import Path
from typing import List, Optional

import pandas as pd
def str_to_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")

# 复用已有的结构化读写工具
CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# 全角空格 → 普通空格
FULLWIDTH_SPACE = "　"

# 全角 ASCII 字符区间 U+FF01-U+FF5E → U+0021-U+007E（偏移量 0xFEE0）
_FW_START = 0xFF01
_FW_END = 0xFF5E
_FW_OFFSET = 0xFEE0

# 预计算全角→半角映射表
_FULLWIDTH_TO_HALFWIDTH = {}
for cp in range(_FW_START, _FW_END + 1):
    _FULLWIDTH_TO_HALFWIDTH[chr(cp)] = chr(cp - _FW_OFFSET)
_FULLWIDTH_TO_HALFWIDTH[FULLWIDTH_SPACE] = " "

_VALID_NORM_FORMS = {"NFC", "NFD", "NFKC", "NFKD"}


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _normalize_text(text: str, norm_form: Optional[str], keep_newlines: bool) -> str:
    s = text

    # 1. 全角 ASCII 字符 → 半角
    s = s.translate(str.maketrans(_FULLWIDTH_TO_HALFWIDTH))

    # 2. Unicode 正规化（可选）
    if norm_form and norm_form in _VALID_NORM_FORMS:
        s = unicodedata.normalize(norm_form, s)

    # 3. 换行处理
    if not keep_newlines:
        s = s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")

    return s


def normalize_fullwidth(
    df: pd.DataFrame,
    cols: List[str],
    norm_form: Optional[str],
    keep_newlines: bool,
) -> pd.DataFrame:
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: _normalize_text(str(x), norm_form, keep_newlines) if not pd.isna(x) else x
        )
    return result


def run_normalizer(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    norm_form: Optional[str],
    keep_newlines: bool,
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    cleaned = normalize_fullwidth(df, cols=cols, norm_form=norm_form, keep_newlines=keep_newlines)

    write_structured_data(cleaned, output_path)
    msg = (
        f"[OK] 全角/半角规范化完成 -> {output_path}\n"
        f"   文本列: {cols}\n"
        f"   norm_form={norm_form or '无'}, keep_newlines={keep_newlines}"
    )
    print(msg)


def main():
    parser = argparse.ArgumentParser(
        description="全角/半角字符规范化：将全角ASCII字符（字母、数字、标点）转换为半角，可选Unicode正规化"
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
        "--norm_form",
        required=False,
        default=None,
        choices=["NFC", "NFD", "NFKC", "NFKD"],
        help="Unicode正规化形式；默认不执行",
    )
    parser.add_argument(
        "--keep_newlines", type=str_to_bool,
        help="保留换行符（默认折叠为空格）",
    )

    args = parser.parse_args()
    run_normalizer(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        norm_form=args.norm_form,
        keep_newlines=args.keep_newlines,
    )


if __name__ == "__main__":
    main()
