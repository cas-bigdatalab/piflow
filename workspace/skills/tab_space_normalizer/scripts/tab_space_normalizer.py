import argparse, sys, textwrap
from pathlib import Path
from typing import List, Optional
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


def _normalize(text: str, tab_width: int, strip_trailing: bool, dedent: bool) -> str:
    s = text
    if "\t" in s:
        s = s.expandtabs(tab_width)
    if strip_trailing:
        s = "\n".join(line.rstrip() for line in s.splitlines())
    if dedent and s.strip():
        s = textwrap.dedent(s)
    return s


def _select_columns(df, text_columns):
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def run(input_path, output_path, text_columns, tab_width, strip_trailing, dedent):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns) or _select_columns(df, None)
    for col in cols:
        df[col] = df[col].apply(
            lambda x: _normalize(str(x), tab_width, strip_trailing, dedent) if not pd.isna(x) else x
        )
    write_structured_data(df, output_path)
    print(f"[OK] Tab/空格规范化完成 -> {output_path}\n   列: {cols}, tab_width={tab_width}, strip_trailing={strip_trailing}, dedent={dedent}")


def main():
    p = argparse.ArgumentParser(description="Tab/空格规范化：Tab→空格、去行尾空格、去公共缩进")
    p.add_argument("--input_path", required=True)
    p.add_argument("--output_path", required=True)
    p.add_argument("--text_columns", default=None)
    p.add_argument("--tab_width", type=int, default=4)
    p.add_argument("--strip_trailing", type=lambda v: v.lower() in ("true", "1", "yes"), default=True)
    p.add_argument("--dedent", type=lambda v: v.lower() in ("true", "1", "yes"), default=False)
    args = p.parse_args()
    run(args.input_path, args.output_path, args.text_columns, args.tab_width, args.strip_trailing, args.dedent)


if __name__ == "__main__":
    main()
