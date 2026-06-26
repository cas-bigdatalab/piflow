import argparse
import os
import json
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')


def read_data(file_path: str) -> pd.DataFrame:
    """读取数据文件"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    if file_ext == '.csv':
        for encoding in common_encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise Exception("无法读取CSV文件")

    elif file_ext == '.tsv':
        for encoding in common_encodings:
            try:
                return pd.read_csv(file_path, sep='\t', encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise Exception("无法读取TSV文件")

    elif file_ext in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)

    elif file_ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict) and 'data' in data:
            return pd.DataFrame(data['data'])
        else:
            return pd.DataFrame([data])

    elif file_ext == '.jsonl':
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return pd.DataFrame(records)

    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")


def write_data(df: pd.DataFrame, output_path: str):
    """写入数据文件"""
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


class MissingValueHandler:
    """缺失值处理工具类"""

    def __init__(
        self,
        columns: list = None,
        strategy: str = 'drop',
        threshold: float = 0.5
    ):
        self.columns = columns
        self.strategy = strategy
        self.threshold = threshold

    def get_missing_stats(self, df: pd.DataFrame, columns: list) -> dict:
        """获取缺失值统计"""
        stats = {}
        for col in columns:
            missing_count = df[col].isna().sum()
            stats[col] = missing_count
        return stats

    def perform(self, input_path: str, output_path: str):
        """执行缺失值处理"""
        # 读取数据
        df = read_data(input_path)
        total_rows = len(df)

        # 确定要处理的列
        if self.columns:
            missing_cols = [col for col in self.columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"字段不存在: {missing_cols}。可用字段: {list(df.columns)}")
            columns = self.columns
        else:
            columns = df.columns.tolist()

        # 处理前统计
        before_stats = self.get_missing_stats(df, columns)
        total_missing_before = sum(before_stats.values())

        # 执行处理
        if self.strategy == 'drop':
            result_df = df.dropna(subset=columns)

        elif self.strategy == 'drop_cols':
            # 删除缺失比例超阈值的列
            cols_to_drop = []
            for col in columns:
                missing_ratio = df[col].isna().sum() / len(df)
                if missing_ratio > self.threshold:
                    cols_to_drop.append(col)
            result_df = df.drop(columns=cols_to_drop)

        else:
            raise ValueError(f"不支持的处理策略: {self.strategy}")

        # 处理后统计
        result_columns = [col for col in columns if col in result_df.columns]
        after_stats = self.get_missing_stats(result_df, result_columns)
        total_missing_after = sum(after_stats.values())

        # 写入输出
        write_data(result_df, output_path)

        # 输出统计
        columns_str = ', '.join(columns) if columns else 'all fields'
        print(f"\n[OK] Missing value handling completed!")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")
        print(f"   Columns: {columns_str}")
        print(f"   Strategy: {self.strategy}")
        print(f"   Total rows: {total_rows}")
        print(f"   Missing value stats (before):")
        for col, count in before_stats.items():
            pct = count / total_rows * 100 if total_rows > 0 else 0
            print(f"     - {col}: {count} missing ({pct:.1f}%)")
        print(f"   Total missing cells (before): {total_missing_before}")
        print(f"   Output rows: {len(result_df)}")
        print(f"   Missing cells (after): {total_missing_after}")


def main():
    parser = argparse.ArgumentParser(
        description="MissingValueHandler - 缺失值处理工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--columns', type=str, default=None,
                        help='处理字段，逗号分隔')
    parser.add_argument('--strategy', type=str, default='drop',
                        choices=['drop', 'drop_cols'],
                        help='处理策略，默认"drop"')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='删除阈值，默认0.5')

    args = parser.parse_args()

    # 解析字段列表
    columns = None
    if args.columns:
        columns = [s.strip() for s in args.columns.split(',')]

    handler = MissingValueHandler(
        columns=columns,
        strategy=args.strategy,
        threshold=args.threshold
    )

    handler.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
