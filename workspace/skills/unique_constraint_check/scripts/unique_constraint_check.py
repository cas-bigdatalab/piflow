import argparse
from pathlib import Path

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


COMMON_ENCODINGS = ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]


def read_input_table(file_path: str) -> pd.DataFrame:
    file_ext = Path(file_path).suffix.lower()
    if file_ext == ".csv":
        try:
            import chardet  # type: ignore
        except ImportError:
            chardet = None

        test_encodings = COMMON_ENCODINGS[:]
        if chardet is not None:
            with open(file_path, "rb") as f:
                detected = chardet.detect(f.read(10240)).get("encoding")
            if detected:
                test_encodings = [detected] + test_encodings
        test_encodings = list(dict.fromkeys(test_encodings))

        for encoding in test_encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding, dtype=str, keep_default_na=False)
            except (UnicodeDecodeError, LookupError):
                continue
        raise Exception("无法读取CSV文件")

    if file_ext == ".tsv":
        for encoding in COMMON_ENCODINGS:
            try:
                return pd.read_csv(file_path, sep="\t", encoding=encoding, dtype=str, keep_default_na=False)
            except (UnicodeDecodeError, LookupError):
                continue
        raise Exception("无法读取TSV文件")

    if file_ext in [".xls", ".xlsx"]:
        return pd.read_excel(file_path, dtype=str).fillna("")

    if file_ext == ".sav":
        return pd.read_spss(file_path).fillna("").astype(str)

    raise ValueError(f"不支持的文件格式: {file_ext}")


def write_output_table(df: pd.DataFrame, output_path: str) -> None:
    output_dir = Path(output_path).parent
    if str(output_dir) and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def run(input_path, output_path, unique_fields, allow_null, qc_mark, mark_field_name):
    df = read_input_table(input_path)
    mark_field = mark_field_name or "QC0000"
    df[mark_field] = ""

    fields = [f.strip() for f in unique_fields.split(",") if f.strip()]
    missing = [f for f in fields if f not in df.columns]
    if missing:
        print(f"[ERROR] 字段不存在: {missing}")
        sys.exit(1)

    # 多字段时分别检查每个字段的唯一性（非组合键）
    dup_mask = pd.Series(False, index=df.index)
    all_issues = []

    for f in fields:
        vals = df[f].astype(str).str.strip()
        if allow_null:
            is_null = vals.isin(["", "nan", "None", "NA", "null"])
            single_mask = pd.Series(False, index=df.index)
            non_null_vals = vals[~is_null]
            if len(non_null_vals) > 0:
                single_mask.loc[~is_null] = non_null_vals.duplicated(keep="first").to_numpy()
        else:
            single_mask = vals.duplicated(keep="first")
        if single_mask.any():
            dups = vals[single_mask].unique()[:3]
            all_issues.append(f"[{f}] {single_mask.sum()} 行重复，示例: {list(dups)}")
            dup_mask |= single_mask

    if dup_mask.any():
        df.loc[dup_mask, mark_field] = qc_mark
        print(f"[QC FAIL] 唯一性约束未通过 ({len(all_issues)} 项):")
        for i in all_issues:
            print(f"  {i}")
    else:
        print(f"[QC PASS] 唯一性约束通过 (字段: {fields})")

    write_output_table(df, output_path)
    print(f"[OK] 结果已写入 -> {output_path}")


def main():
    p = argparse.ArgumentParser(description="唯一性约束校验")
    p.add_argument("--input_path", required=True)
    p.add_argument("--output_path", required=True)
    p.add_argument("--unique_fields", required=True, help="唯一字段，逗号分隔组合")
    p.add_argument("--allow_null", type=str_to_bool, default=False, help="允许多个空值，空值不视为重复")
    p.add_argument("--qc_mark", required=True)
    p.add_argument("--mark_field_name", default="QC0000")
    args = p.parse_args()
    run(args.input_path, args.output_path, args.unique_fields, args.allow_null, args.qc_mark, args.mark_field_name)


if __name__ == "__main__":
    main()
