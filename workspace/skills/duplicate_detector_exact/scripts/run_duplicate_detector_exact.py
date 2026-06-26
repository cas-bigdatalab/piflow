import argparse
import os
import json
import pandas as pd
import warnings

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

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


class DuplicateDetector:
    """重复数据检测工具类"""

    def __init__(
        self,
        subset: list = None,
        keep: str = 'first'
    ):
        self.subset = subset
        self.keep = keep

    def exact_duplicate_detection(self, df: pd.DataFrame) -> pd.DataFrame:
        """精确匹配去重"""
        if self.keep == 'mark':
            df = df.copy()
            df['is_duplicate'] = df.duplicated(subset=self.subset, keep='first')
            return df
        elif self.keep == 'none':
            return df.drop_duplicates(subset=self.subset, keep=False)
        else:
            return df.drop_duplicates(subset=self.subset, keep=self.keep)

    def perform(self, input_path: str, output_path: str):
        """执行重复检测"""
        df = read_data(input_path)
        total_rows = len(df)

        if self.subset:
            missing_cols = [col for col in self.subset if col not in df.columns]
            if missing_cols:
                raise ValueError(f"字段不存在: {missing_cols}。可用字段: {list(df.columns)}")

        result_df = self.exact_duplicate_detection(df)

        if self.keep == 'mark':
            duplicate_count = result_df['is_duplicate'].sum()
            output_rows = len(result_df)
        else:
            duplicate_count = total_rows - len(result_df)
            output_rows = len(result_df)

        write_data(result_df, output_path)

        subset_str = ', '.join(self.subset) if self.subset else 'all fields'
        print(f"\n[OK] Duplicate detection completed!")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")
        print(f"   Subset fields: {subset_str}")
        print(f"   Keep strategy: {self.keep}")
        print(f"   Total rows: {total_rows}")
        print(f"   Duplicate rows: {duplicate_count}")
        print(f"   Output rows: {output_rows}")


def main():
    parser = argparse.ArgumentParser(
        description="DuplicateDetector - 重复数据检测工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--subset', type=str, default=None,
                        help='判断重复的字段，逗号分隔')
    parser.add_argument('--keep', type=str, default='first',
                        choices=['first', 'last', 'none', 'mark'],
                        help='保留策略，默认"first"')

    args = parser.parse_args()

    subset = None
    if args.subset:
        subset = [s.strip() for s in args.subset.split(',')]

    detector = DuplicateDetector(
        subset=subset,
        keep=args.keep,
    )

    detector.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
