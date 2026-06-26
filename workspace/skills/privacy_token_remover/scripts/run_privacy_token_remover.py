import argparse
import re
import sys
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

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IP_PATTERN = re.compile(
    r"\b(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}\b"
)
PHONE_PATTERN = re.compile(r"\b\d{3}[- ]?\d{3,4}[- ]?\d{4}\b")


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _clean_text(
    text: str,
    remove_email: bool,
    remove_ip: bool,
    remove_phone: bool,
    replace_token: str,
) -> str:
    cleaned = text
    if remove_email:
        cleaned = EMAIL_PATTERN.sub(replace_token, cleaned)
    if remove_ip:
        cleaned = IP_PATTERN.sub(replace_token, cleaned)
    if remove_phone:
        cleaned = PHONE_PATTERN.sub(replace_token, cleaned)
    return cleaned


def remove_privacy_tokens(
    df: pd.DataFrame,
    cols: List[str],
    remove_email: bool,
    remove_ip: bool,
    remove_phone: bool,
    replace_token: str,
) -> pd.DataFrame:
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: _clean_text(
                str(x),
                remove_email=remove_email,
                remove_ip=remove_ip,
                remove_phone=remove_phone,
                replace_token=replace_token,
            )
            if not pd.isna(x)
            else x
        )
    return result


def run_cleaner(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    remove_email: bool,
    remove_ip: bool,
    remove_phone: bool,
    replace_token: str,
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    cleaned = remove_privacy_tokens(
        df,
        cols=cols,
        remove_email=remove_email,
        remove_ip=remove_ip,
        remove_phone=remove_phone,
        replace_token=replace_token,
    )

    write_structured_data(cleaned, output_path)
    print(
        f"[OK] 隐私标识清理完成 -> {output_path}\n"
        f"   处理列: {cols}\n"
        f"   选项: email={remove_email}, ip={remove_ip}, phone={remove_phone}, replace='{replace_token}'"
    )


def main():
    parser = argparse.ArgumentParser(description="隐私标识清理：移除或替换邮件/IP/电话等网络隐私标识")
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--text_columns", required=False, default=None, help="处理的文本列，逗号分隔；默认全部字符串列")
    parser.add_argument("--remove_email", type=str_to_bool, default=False, help="移除邮箱，默认关闭")
    parser.add_argument("--remove_ip", type=str_to_bool, default=False, help="移除IP，默认关闭")
    parser.add_argument("--remove_phone", type=str_to_bool, default=False, help="移除电话，默认关闭")
    parser.add_argument("--replace_token", default="", help="替换文本（默认删除），如 '[REMOVED]'")

    args = parser.parse_args()

    run_cleaner(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        remove_email=args.remove_email,
        remove_ip=args.remove_ip,
        remove_phone=args.remove_phone,
        replace_token=args.replace_token,
    )


if __name__ == "__main__":
    main()
