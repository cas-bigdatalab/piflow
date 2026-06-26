import argparse
import os
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


class DataMerge:
    """
    数据合并工具类
    支持纵向拼接（concat）和横向关联（join）
    支持 Dask 处理海量数据
    """

    def __init__(
        self,
        merge_type: str = 'concat',
        join_key: str = None,
        join_how: str = 'inner',
        ignore_index: bool = True,
        use_dask: bool = False,
        blocksize: str = '64MB'
    ):
        self.merge_type = merge_type
        self.join_key = join_key
        self.join_how = join_how
        self.ignore_index = ignore_index
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
            # 不支持的格式回退到 pandas
            return dd.from_pandas(read_structured_data(file_path), npartitions=4)

    def perform(self, input_files: list, output_path: str):
        """
        执行数据合并操作

        :param input_files: 输入文件路径列表
        :param output_path: 输出文件路径
        """
        if len(input_files) < 2:
            raise ValueError("至少需要2个文件进行合并")

        if self.use_dask:
            self._perform_dask(input_files, output_path)
        else:
            self._perform_pandas(input_files, output_path)

    def _perform_pandas(self, input_files: list, output_path: str):
        """使用 pandas 处理（小数据）"""
        dfs = []
        rows_before = []
        for file_path in input_files:
            df = read_structured_data(file_path)
            dfs.append(df)
            rows_before.append(len(df))
            print(f"   读取文件: {file_path}, 行数: {len(df)}, 列数: {len(df.columns)}")

        if self.merge_type == 'concat':
            result_df = pd.concat(dfs, ignore_index=self.ignore_index)
        elif self.merge_type == 'join':
            if not self.join_key:
                raise ValueError("横向关联模式需要指定join_key参数")
            result_df = dfs[0]
            for i, df in enumerate(dfs[1:], 1):
                result_df = pd.merge(result_df, df, on=self.join_key, how=self.join_how, suffixes=('', f'_{i}'))
        else:
            raise ValueError(f"不支持的合并类型: {self.merge_type}")

        write_structured_data(result_df, output_path)
        self._print_result(len(input_files), rows_before, len(result_df), len(result_df.columns), output_path, 'pandas')

    def _perform_dask(self, input_files: list, output_path: str):
        """使用 Dask 处理（大数据）"""
        dfs = []
        for file_path in input_files:
            df = self._read_dask(file_path)
            dfs.append(df)
            print(f"   读取文件: {file_path} (Dask lazy load)")

        if self.merge_type == 'concat':
            result_df = dd.concat(dfs, ignore_unknown_divisions=True)
        elif self.merge_type == 'join':
            if not self.join_key:
                raise ValueError("横向关联模式需要指定join_key参数")
            result_df = dfs[0]
            for i, df in enumerate(dfs[1:], 1):
                result_df = dd.merge(result_df, df, on=self.join_key, how=self.join_how, suffixes=('', f'_{i}'))
        else:
            raise ValueError(f"不支持的合并类型: {self.merge_type}")

        # 写入输出
        file_ext = os.path.splitext(output_path)[1].lower()
        if file_ext == '.csv':
            result_df.to_csv(output_path, index=False, single_file=True)
        elif file_ext == '.parquet':
            result_df.to_parquet(output_path)
        else:
            # 其他格式先计算再用 pandas 写入
            write_structured_data(result_df.compute(), output_path)

        total_rows = len(result_df)
        total_cols = len(result_df.columns)
        self._print_result(len(input_files), ['(lazy)'] * len(input_files), total_rows, total_cols, output_path, 'dask')

    def _print_result(self, num_files, rows_before, total_rows, total_cols, output_path, engine):
        print(f"\n[OK] Data merge completed!")
        print(f"   Engine: {engine}")
        print(f"   Merge type: {self.merge_type}")
        print(f"   Input files: {num_files}")
        print(f"   Total rows before merge: {', '.join(map(str, rows_before))}")
        print(f"   Total rows after merge: {total_rows}")
        print(f"   Total columns after merge: {total_cols}")
        print(f"   Output file: {output_path}")


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
        description="DataMergeConcat - 数据纵向拼接工具"
    )

    parser.add_argument('--input_files', required=True, type=str,
                        help='输入文件路径列表，多个文件用逗号分隔')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--ignore_index', type=str_to_bool, default=True,
                        help='纵向拼接时是否忽略原索引，默认True')
    parser.add_argument('--use_dask', type=str_to_bool, default=False,
                        help='是否使用Dask处理大数据，默认False')
    parser.add_argument('--blocksize', type=str, default='64MB',
                        help='Dask分块大小，默认64MB')

    args = parser.parse_args()

    # 解析输入文件列表
    input_files = [f.strip() for f in args.input_files.split(',')]

    merger = DataMerge(
        merge_type='concat',
        join_key=None,
        join_how='inner',
        ignore_index=args.ignore_index,
        use_dask=args.use_dask,
        blocksize=args.blocksize
    )

    merger.perform(input_files=input_files, output_path=args.output)


if __name__ == '__main__':
    main()
