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
        df.to_json(output_path, orient='records', force_ascii=False, indent=2, date_format='iso')
    elif file_ext == '.jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                f.write(json.dumps(row.to_dict(), ensure_ascii=False, default=str) + '\n')
    else:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')


class DataTypeConverter:
    """数据类型转换工具类"""

    def __init__(
        self,
        conversions: dict,
        date_format: str = '%Y-%m-%d',
        errors: str = 'coerce'
    ):
        self.conversions = conversions
        self.date_format = date_format
        self.errors = errors

    def convert_column(self, series: pd.Series, target_type: str) -> tuple:
        """转换单列类型"""
        original_type = str(series.dtype)
        error_count = 0

        if target_type == 'int':
            if self.errors == 'coerce':
                converted = pd.to_numeric(series, errors='coerce')
                error_count = converted.isna().sum() - series.isna().sum()
                converted = converted.astype('Int64')  # nullable int
            elif self.errors == 'ignore':
                try:
                    converted = series.astype(int)
                except:
                    converted = series
            else:
                converted = series.astype(int)

        elif target_type == 'float':
            if self.errors == 'coerce':
                converted = pd.to_numeric(series, errors='coerce')
                error_count = converted.isna().sum() - series.isna().sum()
            elif self.errors == 'ignore':
                try:
                    converted = series.astype(float)
                except:
                    converted = series
            else:
                converted = series.astype(float)

        elif target_type == 'str':
            converted = series.astype(str)
            converted = converted.replace('nan', '')
            converted = converted.replace('None', '')

        elif target_type == 'datetime':
            if self.errors == 'coerce':
                converted = pd.to_datetime(series, format=self.date_format, errors='coerce')
                error_count = converted.isna().sum() - series.isna().sum()
            elif self.errors == 'ignore':
                try:
                    converted = pd.to_datetime(series, format=self.date_format)
                except:
                    converted = series
            else:
                converted = pd.to_datetime(series, format=self.date_format)

        elif target_type == 'bool':
            # 处理常见的布尔值表示
            bool_map = {
                'true': True, 'false': False,
                'True': True, 'False': False,
                'TRUE': True, 'FALSE': False,
                '1': True, '0': False,
                1: True, 0: False,
                'yes': True, 'no': False,
                'Yes': True, 'No': False,
                'Y': True, 'N': False,
                'y': True, 'n': False,
            }
            converted = series.map(lambda x: bool_map.get(x, x) if pd.notna(x) else x)
            converted = converted.astype('boolean')

        elif target_type == 'category':
            converted = series.astype('category')

        else:
            raise ValueError(f"不支持的目标类型: {target_type}")

        return converted, original_type, str(converted.dtype), max(0, error_count)

    def perform(self, input_path: str, output_path: str):
        """执行类型转换"""
        # 读取数据
        df = read_data(input_path)
        total_rows = len(df)

        # 验证字段
        missing_cols = [col for col in self.conversions.keys() if col not in df.columns]
        if missing_cols:
            raise ValueError(f"字段不存在: {missing_cols}。可用字段: {list(df.columns)}")

        # 执行转换
        conversion_results = []
        total_errors = 0

        for col, target_type in self.conversions.items():
            converted, orig_type, new_type, errors = self.convert_column(df[col], target_type)
            df[col] = converted
            conversion_results.append({
                'column': col,
                'from': orig_type,
                'to': new_type,
                'errors': errors
            })
            total_errors += errors

        # 写入输出
        write_data(df, output_path)

        # 输出统计
        print(f"\n[OK] Data type conversion completed!")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")
        print(f"   Conversions:")
        for result in conversion_results:
            print(f"     - {result['column']}: {result['from']} → {result['to']}")
        print(f"   Total rows: {total_rows}")
        print(f"   Conversion errors: {total_errors}")


def main():
    parser = argparse.ArgumentParser(
        description="DataTypeConverter - 数据类型转换工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--conversions', required=True, type=str,
                        help='转换规则，格式：字段名:目标类型，逗号分隔')
    parser.add_argument('--date_format', type=str, default='%Y-%m-%d',
                        help='日期格式，默认"%%Y-%%m-%%d"')
    parser.add_argument('--errors', type=str, default='coerce',
                        choices=['raise', 'coerce', 'ignore'],
                        help='错误处理方式，默认"coerce"')

    args = parser.parse_args()

    # 解析转换规则
    conversions = {}
    for item in args.conversions.split(','):
        parts = item.strip().split(':')
        if len(parts) == 2:
            col, dtype = parts[0].strip(), parts[1].strip()
            conversions[col] = dtype

    if not conversions:
        raise ValueError("请提供有效的转换规则")

    converter = DataTypeConverter(
        conversions=conversions,
        date_format=args.date_format,
        errors=args.errors
    )

    converter.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
