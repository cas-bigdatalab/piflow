import argparse
import re
import sys
from pathlib import Path
from typing import Callable, List, Optional

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

# 日期正则
CN_DATE_RE = re.compile(r"(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?")
YMD_RE = re.compile(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})")
MDY_DMY_RE = re.compile(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})")

# 货币正则
CURRENCY_MAP = {
    "$": "USD",
    "€": "EUR",
    "¥": "CNY",
    "￥": "CNY",
}
CURRENCY_RE = re.compile(r"([$€¥￥])\s?([+-]?\d[\d,]*\.?\d*)")


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _pad(num_str: str) -> str:
    return num_str.zfill(2)


def _normalize_ymd(match: re.Match) -> str:
    y, m, d = match.groups()
    return f"{y}-{_pad(m)}-{_pad(d)}"


def _normalize_mdy_dmy(match: re.Match) -> str:
    a, b, y = match.groups()
    first = int(a)
    second = int(b)
    # 简单规则：如果第一段>12，则视为日-月-年；否则视为月-日-年
    if first > 12:
        d, m = first, second
    else:
        m, d = first, second
    return f"{y}-{_pad(str(m))}-{_pad(str(d))}"


def normalize_dates(text: str) -> str:
    s = CN_DATE_RE.sub(_normalize_ymd, text)
    s = YMD_RE.sub(_normalize_ymd, s)
    s = MDY_DMY_RE.sub(_normalize_mdy_dmy, s)
    return s


def _normalize_currency(match: re.Match) -> str:
    symbol, amount_raw = match.groups()
    code = CURRENCY_MAP.get(symbol, symbol)
    amount = amount_raw.replace(",", "")
    return f"{code} {amount}"


def normalize_currencies(text: str) -> str:
    return CURRENCY_RE.sub(_normalize_currency, text)


def normalize_text(
    text: str,
    normalize_date: bool,
    normalize_currency: bool,
) -> str:
    s = text
    if normalize_date:
        s = normalize_dates(s)
    if normalize_currency:
        s = normalize_currencies(s)
    return s


def normalize_dataframe(
    df: pd.DataFrame,
    cols: List[str],
    normalize_date: bool,
    normalize_currency: bool,
) -> pd.DataFrame:
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: normalize_text(str(x), normalize_date, normalize_currency) if not pd.isna(x) else x
        )
    return result


def run_normalizer(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    normalize_date: bool,
    normalize_currency_flag: bool,
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    cleaned = normalize_dataframe(
        df,
        cols=cols,
        normalize_date=normalize_date,
        normalize_currency=normalize_currency_flag,
    )

    write_structured_data(cleaned, output_path)
    print(
        f"[OK] 时间/货币归一完成 -> {output_path}\n"
        f"   文本列: {cols}\n"
        f"   normalize_date={normalize_date}, normalize_currency={normalize_currency_flag}"
    )


def main():
    parser = argparse.ArgumentParser(description="时间/货币归一：规范日期格式为 YYYY-MM-DD，货币符号为标准币种+数值")
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--text_columns", required=False, default=None, help="处理的文本列，逗号分隔；默认全部字符串列")
    parser.add_argument("--disable_date", type=str_to_bool, help="关闭日期归一")
    parser.add_argument("--disable_currency", type=str_to_bool, help="关闭货币归一")

    args = parser.parse_args()

    run_normalizer(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        normalize_date=not args.disable_date,
        normalize_currency_flag=not args.disable_currency,
    )


if __name__ == "__main__":
    main()
