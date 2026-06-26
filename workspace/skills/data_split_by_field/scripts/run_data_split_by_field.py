import argparse
import os
import re
import warnings

try:
    import dask.dataframe as dd
    DASK_AVAILABLE = True
except ImportError:
    DASK_AVAILABLE = False

import pandas as pd

try:
    import chardet
except ImportError:
    chardet = None

warnings.filterwarnings('ignore')


def read_structured_data(file_path: str) -> pd.DataFrame:
    """
    读取结构化数据文件并返回pandas DataFrame
    支持CSV、TSV、Excel、SPSS等格式，自动检测编码
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    try:
        if file_ext == '.csv':
            detected_encoding = None
            if chardet is not None:
                with open(file_path, 'rb') as f:
                    raw_data = f.read(10240)
                    detected_encoding = chardet.detect(raw_data)['encoding']

            df = None
            test_encodings = [detected_encoding] + common_encodings if detected_encoding else common_encodings
            test_encodings = list(dict.fromkeys(test_encodings))

            for encoding in test_encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue

            if df is None:
                raise Exception("所有编码尝试均失败，无法读取CSV文件")

        elif file_ext == '.tsv':
            df = None
            for encoding in common_encodings:
                try:
                    df = pd.read_csv(file_path, sep='\t', encoding=encoding)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            if df is None:
                raise Exception("所有编码尝试均失败，无法读取TSV文件")

        elif file_ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')

        elif file_ext == '.sav':
            df = pd.read_spss(file_path)

        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        return df

    except Exception as e:
        raise Exception(f"读取文件失败: {str(e)}") from e


def write_structured_data(df: pd.DataFrame, output_path: str, **kwargs) -> None:
    """
    将DataFrame写入指定路径的结构化数据文件
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("输入数据必须是pandas DataFrame类型")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_ext = os.path.splitext(output_path)[1].lower()
    write_kwargs = {'index': False}
    write_kwargs.update(kwargs)

    try:
        if file_ext == '.csv':
            df.to_csv(output_path, **write_kwargs)
        elif file_ext == '.tsv':
            df.to_csv(output_path, sep='\t', **write_kwargs)
        elif file_ext == '.xls':
            df.to_excel(output_path, engine='xlwt', **write_kwargs)
        elif file_ext == '.xlsx':
            df.to_excel(output_path, engine='openpyxl', **write_kwargs)
        elif file_ext == '.sav':
            df.to_spss(output_path, **write_kwargs)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    except Exception as e:
        raise Exception(f"写入文件失败: {str(e)}") from e


def sanitize_filename(value: str) -> str:
    """
    将字段值转换为安全的文件名
    替换特殊字符为下划线
    """
    # 转换为字符串
    value = str(value)
    # 替换特殊字符
    value = re.sub(r'[\\/*?:"<>|]', '_', value)
    # 替换空格
    value = value.replace(' ', '_')
    # 限制长度
    if len(value) > 50:
        value = value[:50]
    return value


class DataSplitByField:
    """
    按字段拆分数据工具类
    根据指定字段的值将数据拆分为多个文件
    支持 Dask 处理海量数据
    """

    def __init__(
        self,
        split_field: str,
        output_prefix: str = 'split',
        output_format: str = 'csv',
        use_dask: bool = False,
        blocksize: str = '64MB'
    ):
        self.split_field = split_field
        self.output_prefix = output_prefix
        self.output_format = output_format.lower()
        self.use_dask = use_dask and DASK_AVAILABLE
        self.blocksize = blocksize

        if use_dask and not DASK_AVAILABLE:
            print("[WARN] Dask not available, falling back to pandas")

    def _read_dask(self, file_path: str):
        """使用 Dask 读取文件"""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.csv':
            return dd.read_csv(file_path, blocksize=self.blocksize)
        elif file_ext == '.tsv':
            return dd.read_csv(file_path, sep='\t', blocksize=self.blocksize)
        elif file_ext in ['.parquet', '.pq']:
            return dd.read_parquet(file_path)
        else:
            return dd.from_pandas(read_structured_data(file_path), npartitions=4)

    def perform(self, input_path: str, output_dir: str):
        """
        执行数据拆分操作

        :param input_path: 输入文件路径
        :param output_dir: 输出目录路径
        """
        if self.use_dask:
            self._perform_dask(input_path, output_dir)
        else:
            self._perform_pandas(input_path, output_dir)

    def _perform_pandas(self, input_path: str, output_dir: str):
        """使用 pandas 处理"""
        df = read_structured_data(input_path)
        total_rows = len(df)

        if self.split_field not in df.columns:
            raise ValueError(f"字段 '{self.split_field}' 不存在于数据中。可用字段: {list(df.columns)}")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        grouped = df.groupby(self.split_field)
        unique_values = df[self.split_field].nunique()
        output_files = []

        for value, group_df in grouped:
            safe_value = sanitize_filename(value)
            output_filename = f"{self.output_prefix}_{safe_value}.{self.output_format}"
            output_path = os.path.join(output_dir, output_filename)
            write_structured_data(group_df, output_path)
            output_files.append((output_path, len(group_df)))

        self._print_result(input_path, total_rows, unique_values, output_files, 'pandas')

    def _perform_dask(self, input_path: str, output_dir: str):
        """使用 Dask 处理大数据"""
        ddf = self._read_dask(input_path)

        if self.split_field not in ddf.columns:
            raise ValueError(f"字段 '{self.split_field}' 不存在于数据中。可用字段: {list(ddf.columns)}")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 获取唯一值
        unique_values = ddf[self.split_field].unique().compute().tolist()
        total_rows = len(ddf)
        output_files = []

        for value in unique_values:
            subset = ddf[ddf[self.split_field] == value]
            safe_value = sanitize_filename(str(value))
            output_filename = f"{self.output_prefix}_{safe_value}.{self.output_format}"
            output_path = os.path.join(output_dir, output_filename)

            if self.output_format == 'csv':
                subset.to_csv(output_path, index=False, single_file=True)
            elif self.output_format == 'parquet':
                subset.to_parquet(output_path)
            else:
                write_structured_data(subset.compute(), output_path)

            row_count = len(subset)
            output_files.append((output_path, row_count))

        self._print_result(input_path, total_rows, len(unique_values), output_files, 'dask')

    def _print_result(self, input_path, total_rows, unique_values, output_files, engine):
        print(f"\n[OK] Data split completed!")
        print(f"   Engine: {engine}")
        print(f"   Input file: {input_path}")
        print(f"   Split field: {self.split_field}")
        print(f"   Total rows: {total_rows}")
        print(f"   Unique values: {unique_values}")
        print(f"   Output files:")
        for file_path, row_count in output_files:
            print(f"     - {file_path} ({row_count} rows)")


def str_to_bool(value):
    """将字符串转换为布尔值"""
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', '1', 'yes'):
        return True
    elif value.lower() in ('false', '0', 'no'):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def main():
    parser = argparse.ArgumentParser(
        description="DataSplitByField - 按字段拆分数据工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output_dir', required=True, type=str,
                        help='输出目录路径')
    parser.add_argument('--split_field', required=True, type=str,
                        help='用于拆分的字段名')
    parser.add_argument('--output_prefix', type=str, default='split',
                        help='输出文件名前缀，默认"split"')
    parser.add_argument('--output_format', type=str, default='csv',
                        choices=['csv', 'tsv', 'xlsx', 'parquet'],
                        help='输出文件格式，默认"csv"')
    parser.add_argument('--use_dask', type=str_to_bool, default=False,
                        help='是否使用Dask处理大数据，默认False')
    parser.add_argument('--blocksize', type=str, default='64MB',
                        help='Dask分块大小，默认64MB')

    args = parser.parse_args()

    splitter = DataSplitByField(
        split_field=args.split_field,
        output_prefix=args.output_prefix,
        output_format=args.output_format,
        use_dask=args.use_dask,
        blocksize=args.blocksize
    )

    splitter.perform(input_path=args.input, output_dir=args.output_dir)


if __name__ == '__main__':
    main()
