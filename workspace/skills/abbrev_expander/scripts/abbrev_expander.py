import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

DEFAULT_DICT: Dict[str, str] = {
    "AI": "artificial intelligence",
    "NLP": "natural language processing",
    "CPU": "central processing unit",
    "GPU": "graphics processing unit",
    "ML": "machine learning",
}


def _load_dict(dict_path: Optional[str]) -> Dict[str, str]:
    if not dict_path:
        return DEFAULT_DICT
    path = Path(dict_path)
    if not path.exists():
        raise FileNotFoundError(f"词典文件不存在: {path}")
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsn"}:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
        raise ValueError("JSON 词典需为 {abbr: full} 映射")
    # CSV/TSV: 期望两列 abbrev,full
    if suffix in {".csv", ".tsv"}:
        sep = "," if suffix == ".csv" else "\t"
        df = pd.read_csv(path, sep=sep)
        required = {"abbrev", "full"}
        if not required.issubset(set(df.columns)):
            raise ValueError("CSV/TSV 需包含列: abbrev, full")
        return {str(a): str(b) for a, b in zip(df["abbrev"], df["full"])}
    raise ValueError("词典格式不支持，仅支持 json/csv/tsv")


def _compile_patterns(mapping: Dict[str, str]) -> List[Tuple[re.Pattern, str, str]]:
    items = sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)
    compiled = []
    for abbr, full in items:
        if not abbr or not full:
            continue
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(abbr)}(?![A-Za-z0-9])")
        compiled.append((pattern, abbr, full))
    return compiled


def _expand_text(text: str, patterns: List[Tuple[re.Pattern, str, str]], keep_abbr: bool) -> str:
    s = text
    for pattern, abbr, full in patterns:
        if keep_abbr:
            def repl(m, a=abbr, f=full):
                token = m.group(0)
                if token.isupper() and token != a.upper():
                    return token
                return f"{f} ({token})"
        else:
            def repl(m, a=abbr, f=full):
                token = m.group(0)
                if token.isupper() and token != a.upper():
                    return token
                return f
        s = pattern.sub(repl, s)
    return s


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def expand_abbrev(
    df: pd.DataFrame,
    cols: List[str],
    mapping: Dict[str, str],
    keep_abbr: bool,
) -> pd.DataFrame:
    patterns = _compile_patterns(mapping)
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: _expand_text(str(x), patterns, keep_abbr) if not pd.isna(x) else x
        )
    return result


def run_expander(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    dict_path: Optional[str],
    keep_abbr: bool,
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    mapping = _load_dict(dict_path)
    expanded = expand_abbrev(df, cols=cols, mapping=mapping, keep_abbr=keep_abbr)

    write_structured_data(expanded, output_path)
    print(
        f"[OK] 领域缩略语展开完成 -> {output_path}\n"
        f"   文本列: {cols}\n"
        f"   词典大小: {len(mapping)}\n"
        f"   keep_abbr={keep_abbr}"
    )


def main():
    parser = argparse.ArgumentParser(description="领域缩略语展开：按词典将缩略语替换为全称，可选保留原缩写")
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--text_columns", required=False, default=None, help="处理的文本列，逗号分隔；默认全部字符串列")
    parser.add_argument("--dict_path", required=False, default=None, help="词典文件 json/csv/tsv（列名 abbrev,full）")
    parser.add_argument("--keep_abbr", type=str_to_bool, help="是否在全称后保留原缩写，如 full (abbr)")

    args = parser.parse_args()
    run_expander(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        dict_path=args.dict_path,
        keep_abbr=args.keep_abbr,
    )


if __name__ == "__main__":
    main()
