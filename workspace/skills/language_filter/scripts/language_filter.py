import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

# langdetect 轻量语言检测
try:
    from langdetect import detect
except ImportError as e:
    raise ImportError("langdetect 未安装，请先安装: pip install langdetect") from e

# 复用已有的结构化读写工具
CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


SUPPORTED_LANGS = {
    "zh": "Chinese",
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
}


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _detect_lang_safe(text: str) -> Optional[str]:
    try:
        return detect(text)
    except Exception:
        return None


def language_filter(df: pd.DataFrame, target_lang: str, text_columns: List[str], keep_mode: bool) -> pd.DataFrame:
    lang_codes = []
    for _, row in df.iterrows():
        concat_text = " ".join([str(row[col]) for col in text_columns if pd.notna(row[col])])
        lang = _detect_lang_safe(concat_text) if concat_text.strip() else None
        lang_codes.append(lang)

    df_out = df.copy()
    df_out["detected_lang"] = lang_codes

    if keep_mode:
        mask = [(lang or "").startswith(target_lang) for lang in lang_codes]
    else:
        mask = [(lang or "") != target_lang and not (lang or "").startswith(target_lang + "-") for lang in lang_codes]

    filtered = df_out[mask].reset_index(drop=True)
    return filtered


def run_language_filter(input_path: str, output_path: str, target_lang: str, text_columns: Optional[str], keep_mode: bool):
    target_lang = target_lang.lower()
    if target_lang not in SUPPORTED_LANGS:
        print(f"[WARN] 目标语种 {target_lang} 不在支持列表 {list(SUPPORTED_LANGS.keys())}，仍将尝试检测。")

    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    filtered = language_filter(df, target_lang=target_lang, text_columns=cols, keep_mode=keep_mode)

    write_structured_data(filtered, output_path)
    print(
        f"[OK] 语种过滤完成 -> {output_path}\n"
        f"   目标语种: {target_lang}\n"
        f"   处理列: {cols}\n"
        f"   输出行数: {len(filtered)} / 原始行数: {len(df)}"
    )


def main():
    parser = argparse.ArgumentParser(description="语种过滤：保留/剔除指定语种文本")
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--target_lang", required=True, help="目标语种代码（如 zh, en, fr 等）")
    parser.add_argument("--text_columns", required=False, default=None, help="用于检测的文本列，逗号分隔；默认全部字符串列")
    parser.add_argument("--mode", choices=["keep", "drop"], default="keep", help="keep=保留目标语种，drop=剔除目标语种")

    args = parser.parse_args()
    run_language_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        target_lang=args.target_lang,
        text_columns=args.text_columns,
        keep_mode=(args.mode == "keep"),
    )


if __name__ == "__main__":
    main()
