import json
import os
from typing import Any, Dict, List

import pandas as pd


def _records_from_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    records = []
    for record in df.to_dict(orient="records"):
        cleaned = {key: (None if pd.isna(value) else value) for key, value in record.items()}
        records.append(cleaned)
    return records


def _read_json_file(file_path: str) -> pd.DataFrame:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return pd.DataFrame()
    data = json.loads(text)
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            return pd.DataFrame(data["data"])
        if isinstance(data.get("records"), list):
            return pd.DataFrame(data["records"])
        return pd.DataFrame([data])
    return pd.DataFrame([{"value": data}])


def _read_jsonl_file(file_path: str) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            item = json.loads(stripped)
            if isinstance(item, dict):
                records.append(item)
            elif isinstance(item, list):
                records.extend([row for row in item if isinstance(row, dict)])
            else:
                records.append({"value": item})
    return pd.DataFrame(records)


def read_structured_data(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == ".csv":
        return pd.read_csv(file_path)
    if file_ext == ".tsv":
        return pd.read_csv(file_path, sep="\t")
    if file_ext == ".jsonl":
        return _read_jsonl_file(file_path)
    if file_ext == ".json":
        return _read_json_file(file_path)
    if file_ext == ".xlsx":
        return pd.read_excel(file_path, engine="openpyxl")
    if file_ext == ".xls":
        return pd.read_excel(file_path, engine="xlrd")
    if file_ext == ".sav":
        return pd.read_spss(file_path)
    raise ValueError(f"不支持的文件格式: {file_ext}")


def write_structured_data(df: pd.DataFrame, output_path: str) -> None:
    if not isinstance(df, pd.DataFrame):
        raise ValueError("输入数据必须是pandas DataFrame类型")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_ext = os.path.splitext(output_path)[1].lower()
    if file_ext == ".csv":
        df.to_csv(output_path, index=False)
    elif file_ext == ".tsv":
        df.to_csv(output_path, index=False, sep="\t")
    elif file_ext == ".jsonl":
        with open(output_path, "w", encoding="utf-8") as f:
            for record in _records_from_dataframe(df):
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    elif file_ext == ".json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(_records_from_dataframe(df), f, ensure_ascii=False, indent=2)
    elif file_ext == ".xlsx":
        df.to_excel(output_path, index=False, engine="openpyxl")
    elif file_ext == ".xls":
        df.to_excel(output_path, index=False, engine="xlwt")
    elif file_ext == ".sav":
        df.to_spss(output_path, index=False)
    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")
