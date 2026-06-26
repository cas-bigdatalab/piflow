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

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

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


class DataMasking:
    """
    数据脱敏工具类
    支持多种脱敏规则：手机号、身份证、姓名、邮箱、银行卡等
    支持 Dask 处理海量数据
    """

    def __init__(
        self,
        masking_rules: dict,
        mask_char: str = '*',
        use_faker: bool = False,
        use_dask: bool = False,
        blocksize: str = '64MB'
    ):
        self.masking_rules = masking_rules
        self.mask_char = mask_char
        self.use_faker = use_faker
        self.use_dask = use_dask and DASK_AVAILABLE
        self.blocksize = blocksize

        if use_dask and not DASK_AVAILABLE:
            print("[WARN] Dask not available, falling back to pandas")

        if use_faker and not FAKER_AVAILABLE:
            raise ImportError("Faker模式需要安装faker库: pip install faker")

        if use_faker:
            self.faker = Faker('zh_CN')

    def _read_dask(self, file_path: str):
        """使用 Dask 读取文件"""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.csv':
            return dd.read_csv(file_path, blocksize=self.blocksize, dtype=str)
        elif file_ext == '.tsv':
            return dd.read_csv(file_path, sep='\t', blocksize=self.blocksize, dtype=str)
        elif file_ext in ['.parquet', '.pq']:
            return dd.read_parquet(file_path)
        else:
            return dd.from_pandas(read_structured_data(file_path), npartitions=4)

    def mask_phone(self, value: str) -> str:
        """手机号脱敏：保留前3后4"""
        if pd.isna(value) or not value:
            return value
        value = str(value)
        if len(value) >= 7:
            return value[:3] + self.mask_char * (len(value) - 7) + value[-4:]
        return self.mask_char * len(value)

    def mask_idcard(self, value: str) -> str:
        """身份证脱敏：保留前6后4"""
        if pd.isna(value) or not value:
            return value
        value = str(value)
        if len(value) >= 10:
            return value[:6] + self.mask_char * (len(value) - 10) + value[-4:]
        return self.mask_char * len(value)

    def mask_name(self, value: str) -> str:
        """姓名脱敏：保留姓，名用*替换"""
        if pd.isna(value) or not value:
            return value
        value = str(value)
        if len(value) >= 2:
            return value[0] + self.mask_char * (len(value) - 1)
        return self.mask_char

    def mask_email(self, value: str) -> str:
        """邮箱脱敏：保留前2和@后部分"""
        if pd.isna(value) or not value:
            return value
        value = str(value)
        if '@' in value:
            local, domain = value.split('@', 1)
            if len(local) > 2:
                local = local[:2] + self.mask_char * (len(local) - 2)
            return f"{local}@{domain}"
        return self.mask_char * len(value)

    def mask_bankcard(self, value: str) -> str:
        """银行卡脱敏：保留前4后4"""
        if pd.isna(value) or not value:
            return value
        value = str(value)
        if len(value) >= 8:
            return value[:4] + self.mask_char * (len(value) - 8) + value[-4:]
        return self.mask_char * len(value)

    def mask_address(self, value: str) -> str:
        """地址脱敏：保留前6个字符"""
        if pd.isna(value) or not value:
            return value
        value = str(value)
        if len(value) > 6:
            return value[:6] + self.mask_char * 3
        return value

    def mask_full(self, value: str) -> str:
        """完全遮蔽"""
        if pd.isna(value) or not value:
            return value
        return self.mask_char * len(str(value))

    def mask_partial(self, value: str) -> str:
        """部分遮蔽：保留首尾"""
        if pd.isna(value) or not value:
            return value
        value = str(value)
        if len(value) > 2:
            return value[0] + self.mask_char * (len(value) - 2) + value[-1]
        return self.mask_char * len(value)

    def faker_phone(self, value: str) -> str:
        """使用Faker生成手机号"""
        return self.faker.phone_number()

    def faker_idcard(self, value: str) -> str:
        """使用Faker生成身份证号"""
        return self.faker.ssn()

    def faker_name(self, value: str) -> str:
        """使用Faker生成姓名"""
        return self.faker.name()

    def faker_email(self, value: str) -> str:
        """使用Faker生成邮箱"""
        return self.faker.email()

    def faker_bankcard(self, value: str) -> str:
        """使用Faker生成银行卡号"""
        return self.faker.credit_card_number()

    def faker_address(self, value: str) -> str:
        """使用Faker生成地址"""
        return self.faker.address()

    def get_masking_func(self, mask_type: str):
        """获取脱敏函数"""
        if self.use_faker:
            faker_funcs = {
                'phone': self.faker_phone,
                'idcard': self.faker_idcard,
                'name': self.faker_name,
                'email': self.faker_email,
                'bankcard': self.faker_bankcard,
                'address': self.faker_address,
            }
            if mask_type in faker_funcs:
                return faker_funcs[mask_type]

        mask_funcs = {
            'phone': self.mask_phone,
            'idcard': self.mask_idcard,
            'name': self.mask_name,
            'email': self.mask_email,
            'bankcard': self.mask_bankcard,
            'address': self.mask_address,
            'full': self.mask_full,
            'partial': self.mask_partial,
        }
        return mask_funcs.get(mask_type, self.mask_partial)

    def perform(self, input_path: str, output_path: str):
        """
        执行数据脱敏操作

        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        """
        if self.use_dask:
            self._perform_dask(input_path, output_path)
        else:
            self._perform_pandas(input_path, output_path)

    def _perform_pandas(self, input_path: str, output_path: str):
        """使用 pandas 处理"""
        df = read_structured_data(input_path)
        total_rows = len(df)

        for field in self.masking_rules.keys():
            if field not in df.columns:
                raise ValueError(f"字段 '{field}' 不存在于数据中。可用字段: {list(df.columns)}")

        masking_stats = {}
        for field, mask_type in self.masking_rules.items():
            mask_func = self.get_masking_func(mask_type)
            original_non_null = df[field].notna().sum()
            df[field] = df[field].apply(mask_func)
            masking_stats[field] = (mask_type, original_non_null)

        write_structured_data(df, output_path)
        self._print_result(input_path, output_path, total_rows, masking_stats, 'pandas')

    def _perform_dask(self, input_path: str, output_path: str):
        """使用 Dask 处理大数据"""
        ddf = self._read_dask(input_path)

        for field in self.masking_rules.keys():
            if field not in ddf.columns:
                raise ValueError(f"字段 '{field}' 不存在于数据中。可用字段: {list(ddf.columns)}")

        total_rows = len(ddf)
        masking_stats = {}

        for field, mask_type in self.masking_rules.items():
            mask_func = self.get_masking_func(mask_type)
            # Dask map_partitions 应用脱敏
            ddf[field] = ddf[field].apply(mask_func, meta=(field, 'object'))
            masking_stats[field] = (mask_type, '(lazy)')

        # 写入输出
        file_ext = os.path.splitext(output_path)[1].lower()
        if file_ext == '.csv':
            ddf.to_csv(output_path, index=False, single_file=True)
        elif file_ext == '.parquet':
            ddf.to_parquet(output_path)
        else:
            write_structured_data(ddf.compute(), output_path)

        self._print_result(input_path, output_path, total_rows, masking_stats, 'dask')

    def _print_result(self, input_path, output_path, total_rows, masking_stats, engine):
        mode = "faker" if self.use_faker else f"mask (char: {self.mask_char})"
        print(f"\n[OK] Data masking completed!")
        print(f"   Engine: {engine}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")
        print(f"   Total rows: {total_rows}")
        print(f"   Masking rules applied:")
        for field, (mask_type, count) in masking_stats.items():
            print(f"     - {field}: {mask_type} ({count} values masked)")
        print(f"   Mode: {mode}")


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


def parse_masking_rules(rules_str: str) -> dict:
    """
    解析脱敏规则字符串
    格式：字段名:脱敏类型,字段名:脱敏类型
    """
    rules = {}
    for rule in rules_str.split(','):
        rule = rule.strip()
        if ':' not in rule:
            raise ValueError(f"无效的脱敏规则格式: {rule}，正确格式: 字段名:脱敏类型")
        field, mask_type = rule.split(':', 1)
        rules[field.strip()] = mask_type.strip()
    return rules


def main():
    parser = argparse.ArgumentParser(
        description="DataMasking - 数据脱敏工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--masking_rules', required=True, type=str,
                        help='脱敏规则，格式：字段名:脱敏类型，多个用逗号分隔')
    parser.add_argument('--mask_char', type=str, default='*',
                        help='脱敏替换字符，默认"*"')

    args = parser.parse_args()

    masking_rules = parse_masking_rules(args.masking_rules)

    masker = DataMasking(
        masking_rules=masking_rules,
        mask_char=args.mask_char,
    )

    masker.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
