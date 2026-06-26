import argparse
import json
import os
import warnings
from typing import Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest

warnings.filterwarnings('ignore')


SUPPORTED_FORMATS = {'.csv', '.tsv', '.xlsx', '.xls', '.json', '.jsonl'}
METHOD_ALIASES = {
    'iqr': 'iqr',
    'zscore': 'zscore',
    'isolation_forest': 'isolation_forest',
    'isolationforest': 'isolation_forest',
    'isolation-forest': 'isolation_forest',
    'ml': 'isolation_forest',
    'group_zscore': 'group_zscore',
    'group_std': 'group_zscore',
    'value_range_consistency': 'group_zscore',
    'qc24': 'group_zscore',
}


def read_data(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'文件不存在: {file_path}')

    file_ext = os.path.splitext(file_path)[1].lower()
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    if file_ext == '.csv':
        for encoding in common_encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise Exception('无法读取CSV文件')

    if file_ext == '.tsv':
        for encoding in common_encodings:
            try:
                return pd.read_csv(file_path, sep='\t', encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise Exception('无法读取TSV文件')

    if file_ext in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)

    if file_ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict) and 'data' in data:
            return pd.DataFrame(data['data'])
        return pd.DataFrame([data])

    if file_ext == '.jsonl':
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return pd.DataFrame(records)

    raise ValueError(f'不支持的文件格式: {file_ext}')


def write_data(df: pd.DataFrame, output_path: str):
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_ext = os.path.splitext(output_path)[1].lower()

    if file_ext == '.csv':
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
    elif file_ext == '.tsv':
        df.to_csv(output_path, sep='\t', index=False, encoding='utf-8-sig')
    elif file_ext in ['.xlsx', '.xls']:
        df.to_excel(output_path, index=False)
    elif file_ext == '.json':
        df.to_json(output_path, orient='records', force_ascii=False, indent=2)
    elif file_ext == '.jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')
    else:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')


def parse_list(value: Optional[str]) -> List[str]:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


def normalize_method(method: str) -> str:
    normalized = METHOD_ALIASES.get(str(method).strip().lower())
    if normalized is None:
        raise ValueError(f'不支持的检测方法: {method}')
    return normalized


def resolve_columns(df: pd.DataFrame, columns: List[str]) -> List[str]:
    if columns:
        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f'字段不存在: {missing_cols}。可用字段: {list(df.columns)}')
        return columns

    numeric_columns = []
    for col in df.columns:
        numeric_series = pd.to_numeric(df[col], errors='coerce')
        if numeric_series.notna().any():
            numeric_columns.append(col)
    if not numeric_columns:
        raise ValueError('未找到可用于检测的数值字段')
    return numeric_columns


def numeric_frame(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    return df[columns].apply(pd.to_numeric, errors='coerce')


def build_flag_frame(index: pd.Index, columns: List[str]) -> pd.DataFrame:
    flag_df = pd.DataFrame(False, index=index, columns=[f'{col}_is_outlier' for col in columns])
    flag_df['is_outlier'] = False
    return flag_df


def detect_iqr(df: pd.DataFrame, columns: List[str], threshold: float):
    numeric_df = numeric_frame(df, columns)
    flag_df = build_flag_frame(df.index, columns)
    bounds = {}

    for col in columns:
        series = numeric_df[col].dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        bounds[col] = (lower, upper)
        col_flags = numeric_df[col].lt(lower) | numeric_df[col].gt(upper)
        flag_df[f'{col}_is_outlier'] = col_flags.fillna(False)
        flag_df['is_outlier'] = flag_df['is_outlier'] | flag_df[f'{col}_is_outlier']

    return flag_df, bounds


def detect_zscore(df: pd.DataFrame, columns: List[str], threshold: float):
    numeric_df = numeric_frame(df, columns)
    flag_df = build_flag_frame(df.index, columns)
    stats_map = {}

    for col in columns:
        series = numeric_df[col].dropna()
        if series.empty:
            continue
        mean = series.mean()
        std = series.std(ddof=0)
        if pd.isna(std) or std == 0:
            continue
        z_scores = (numeric_df[col] - mean).abs() / std
        col_flags = z_scores > threshold
        flag_df[f'{col}_is_outlier'] = col_flags.fillna(False)
        flag_df['is_outlier'] = flag_df['is_outlier'] | flag_df[f'{col}_is_outlier']
        stats_map[col] = (mean, std)

    return flag_df, stats_map


def detect_group_zscore(df: pd.DataFrame, columns: List[str], group_columns: List[str], threshold: float):
    missing_cols = [col for col in group_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f'分组字段不存在: {missing_cols}。可用字段: {list(df.columns)}')

    numeric_df = numeric_frame(df, columns)
    flag_df = build_flag_frame(df.index, columns)
    grouped = df[group_columns].copy()
    grouped['__row_index__'] = df.index
    grouped = grouped.join(numeric_df)

    for col in columns:
        col_flags = pd.Series(False, index=df.index)
        for _, group_df in grouped.groupby(group_columns, dropna=False):
            valid = group_df[col].dropna()
            if len(valid) < 2:
                continue
            mean = valid.mean()
            std = valid.std(ddof=0)
            if pd.isna(std) or std == 0:
                continue
            group_flags = (group_df[col] - mean).abs() > threshold * std
            col_flags.loc[group_df['__row_index__']] = group_flags.fillna(False).values
        flag_df[f'{col}_is_outlier'] = col_flags
        flag_df['is_outlier'] = flag_df['is_outlier'] | col_flags

    return flag_df


def detect_isolation_forest(df: pd.DataFrame, columns: List[str], contamination):
    numeric_df = numeric_frame(df, columns)
    valid_rows = numeric_df.dropna()
    flag_df = build_flag_frame(df.index, columns)

    if valid_rows.empty:
        return flag_df

    if isinstance(contamination, str) and contamination != 'auto':
        contamination = float(contamination)

    clf = IsolationForest(contamination=contamination, random_state=42)
    predictions = clf.fit_predict(valid_rows)
    outlier_index = valid_rows.index[predictions == -1]
    flag_df.loc[outlier_index, 'is_outlier'] = True
    for col in columns:
        flag_df.loc[outlier_index, f'{col}_is_outlier'] = True
    return flag_df


def clip_iqr(df: pd.DataFrame, columns: List[str], threshold: float):
    result_df = df.copy()
    numeric_df = numeric_frame(df, columns)
    for col in columns:
        series = numeric_df[col].dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        result_df[col] = numeric_df[col].clip(lower=lower, upper=upper)
    return result_df


def clip_zscore(df: pd.DataFrame, columns: List[str], threshold: float):
    result_df = df.copy()
    numeric_df = numeric_frame(df, columns)
    for col in columns:
        series = numeric_df[col].dropna()
        if series.empty:
            continue
        mean = series.mean()
        std = series.std(ddof=0)
        if pd.isna(std) or std == 0:
            continue
        lower = mean - threshold * std
        upper = mean + threshold * std
        result_df[col] = numeric_df[col].clip(lower=lower, upper=upper)
    return result_df


def clip_group_zscore(df: pd.DataFrame, columns: List[str], group_columns: List[str], threshold: float):
    result_df = df.copy()
    numeric_df = numeric_frame(df, columns)
    grouped = df[group_columns].copy()
    grouped['__row_index__'] = df.index
    grouped = grouped.join(numeric_df)

    for col in columns:
        for _, group_df in grouped.groupby(group_columns, dropna=False):
            valid = group_df[col].dropna()
            if len(valid) < 2:
                continue
            mean = valid.mean()
            std = valid.std(ddof=0)
            if pd.isna(std) or std == 0:
                continue
            lower = mean - threshold * std
            upper = mean + threshold * std
            rows = group_df['__row_index__']
            result_df.loc[rows, col] = numeric_df.loc[rows, col].clip(lower=lower, upper=upper)
    return result_df


class OutlierDetector:
    def __init__(self, columns: List[str], method: str = 'iqr', threshold: float = 1.5, contamination: float = 0.05, group_columns: Optional[List[str]] = None, action: str = 'mark'):
        self.columns = columns
        self.method = normalize_method(method)
        self.threshold = threshold
        self.contamination = contamination
        self.group_columns = group_columns or []
        self.action = action

    def perform(self, input_path: str, output_path: str):
        df = read_data(input_path)
        total_rows = len(df)
        columns = resolve_columns(df, self.columns)

        if self.method == 'group_zscore' and not self.group_columns:
            raise ValueError('group_zscore 方法必须提供 group_columns')

        if self.method == 'iqr':
            flag_df, _ = detect_iqr(df, columns, self.threshold)
        elif self.method == 'zscore':
            flag_df, _ = detect_zscore(df, columns, self.threshold)
        elif self.method == 'group_zscore':
            flag_df = detect_group_zscore(df, columns, self.group_columns, self.threshold)
        elif self.method == 'isolation_forest':
            flag_df = detect_isolation_forest(df, columns, self.contamination)
        else:
            raise ValueError(f'不支持的检测方法: {self.method}')

        total_outlier_rows = int(flag_df['is_outlier'].sum())

        if self.action == 'mark':
            result_df = df.copy()
            for col in flag_df.columns:
                result_df[col] = flag_df[col]

        elif self.action == 'remove':
            result_df = df.loc[~flag_df['is_outlier']].copy()
            for col in flag_df.columns:
                result_df[col] = flag_df.loc[result_df.index, col]

        elif self.action == 'clip':
            if self.method == 'isolation_forest':
                raise ValueError('--action clip 不支持 isolation_forest，因为它不产生数值边界')
            if self.method == 'iqr':
                result_df = clip_iqr(df, columns, self.threshold)
            elif self.method == 'zscore':
                result_df = clip_zscore(df, columns, self.threshold)
            else:
                result_df = clip_group_zscore(df, columns, self.group_columns, self.threshold)
            for col in flag_df.columns:
                result_df[col] = flag_df[col]

        else:
            raise ValueError(f'不支持的处理方式: {self.action}')

        write_data(result_df, output_path)

        print('\n[OK] Outlier detection completed!')
        print(f'   Input file: {input_path}')
        print(f'   Output file: {output_path}')
        print(f"   Columns: {', '.join(columns)}")
        print(f'   Method: {self.method}')
        if self.method == 'isolation_forest':
            print(f'   Contamination: {self.contamination}')
        else:
            print(f'   Threshold: {self.threshold}')
        if self.group_columns:
            print(f"   Group columns: {', '.join(self.group_columns)}")
        print(f'   Action: {self.action}')
        print(f'   Total rows: {total_rows}')
        print(f'   Total outlier rows: {total_outlier_rows}')
        if self.action == 'remove':
            print(f'   Output rows: {len(result_df)}')


def main():
    parser = argparse.ArgumentParser(description='StatisticalOutlierDetector - 统计与机器学习异常值检测工具')
    parser.add_argument('--input', required=True, type=str, help='输入文件路径')
    parser.add_argument('--output', required=True, type=str, help='输出文件路径')
    parser.add_argument('--columns', required=False, type=str, default='', help='检测字段，逗号分隔；留空时使用所有数值字段')
    parser.add_argument('--method', type=str, default='iqr', choices=['iqr', 'zscore', 'isolation_forest', 'group_zscore', 'isolationforest', 'isolation-forest', 'ml', 'group_std', 'value_range_consistency', 'qc24'], help='检测方法')
    parser.add_argument('--threshold', type=float, default=1.5, help='阈值，默认1.5')
    parser.add_argument('--contamination', type=float, default=0.05, help='IsolationForest异常比例，默认0.05')
    parser.add_argument('--group_columns', required=False, type=str, default='', help='分组字段，group_zscore方法必填')
    parser.add_argument('--action', type=str, default='mark', choices=['mark', 'remove', 'clip'], help='处理方式，默认"mark"')

    args = parser.parse_args()
    columns = parse_list(args.columns)
    group_columns = parse_list(args.group_columns)

    if args.threshold <= 0:
        raise ValueError('threshold 必须大于 0')
    if not (0 < args.contamination <= 0.5):
        raise ValueError('contamination 必须在 0 和 0.5 之间')

    detector = OutlierDetector(
        columns=columns,
        method=args.method,
        threshold=args.threshold,
        contamination=args.contamination,
        group_columns=group_columns,
        action=args.action,
    )
    detector.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
