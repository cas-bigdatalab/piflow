import argparse
import pandas as pd
from typing import List
# 假设data_io.py在同级目录，需确保该文件存在且包含指定方法
from data_io import read_structured_data, write_structured_data


class QC8_DataTypeCheck:
    """
    数据类型检查：检查数据类型是否正确，并标记不合格数据（数值型字段）
    """

    def __init__(self, check_fields_name: str, qc_mark: str, mark_field_name: str):
        self.check_fields_name = check_fields_name  # 检查字段名，逗号分隔
        self.qc_mark = qc_mark  # 质控标识
        self.mark_field_name = mark_field_name  # 质控标识字段名

    def perform(self, input_df: pd.DataFrame) -> pd.DataFrame:
        """
        核心处理逻辑：检查指定字段是否可转换为数值型，标记不合格数据
        :param input_df: 输入DataFrame
        :return: 处理后的DataFrame
        """
        # 解析需要检查的字段列表
        check_fields = [field.strip() for field in self.check_fields_name.split(',') if field.strip()]
        if not check_fields:
            raise ValueError("检查字段列表不能为空，请传入有效的字段名（逗号分隔）")

        # 复制原数据避免修改原DataFrame
        df = input_df.copy()

        # 初始化错误标识列表
        error_conditions = []
        for field_name in check_fields:
            if field_name not in df.columns:
                raise KeyError(f"字段 {field_name} 不存在于输入数据中")

            # 检查字段是否能转换为数值型（模拟Spark的cast(DoubleType)逻辑）
            def is_numeric(val):
                if pd.isna(val):
                    return True  # 空值不判定为错误
                try:
                    float(val)
                    return True
                except (ValueError, TypeError):
                    return False

            # 生成该字段的错误标识（非数值型则标记字段名，否则为None）
            error_series = df[field_name].apply(lambda x: field_name if not is_numeric(x) else None)
            error_conditions.append(error_series)

        # 拼接所有错误字段（逗号分隔）
        inner_concat_errors = pd.Series([''] * len(df))
        for idx, err_series in enumerate(error_conditions):
            if idx == 0:
                inner_concat_errors = err_series.fillna('')
            else:
                inner_concat_errors = inner_concat_errors + ',' + err_series.fillna('')
        # 去除首尾多余的逗号
        inner_concat_errors = inner_concat_errors.str.strip(',').str.replace(',+', ',', regex=True)

        # 格式化质控标识（如：QC8(字段1,字段2)）
        data_quality_issue_formatted = inner_concat_errors.apply(
            lambda x: f"{self.qc_mark}({x})" if x else ''
        )

        # 清理现有的质控标识字段
        if self.mark_field_name in df.columns:
            cleaned_existing_mark = df[self.mark_field_name].astype(str).fillna('').str.strip()
        else:
            cleaned_existing_mark = pd.Series([''] * len(df))

        # 合并新老质控标识
        def merge_marks(existing, new):
            if existing and new:
                return f"{existing};{new}"
            elif existing:
                return existing
            elif new:
                return new
            else:
                return None

        df[self.mark_field_name] = pd.Series(
            [merge_marks(cleaned_existing_mark.iloc[i], data_quality_issue_formatted.iloc[i])
             for i in range(len(df))]
        )

        return df

    @classmethod
    def from_cli_args(cls, args):
        """从命令行参数初始化实例"""
        return cls(
            check_fields_name=args.check_fields_name,
            qc_mark=args.qc_mark,
            mark_field_name=args.mark_field_name
        )


def main():
    """
    命令行调用入口：支持指定输入输出路径及必要参数
    调用示例：
    python QC8_DataTypeCheck.py \
        --input_path ./input_data.parquet \
        --output_path ./output_data.parquet \
        --check_fields_name "field1,field2" \
        --qc_mark "QC8" \
        --mark_field_name "QC0000"
    """
    # 构建命令行参数解析器
    parser = argparse.ArgumentParser(description="数据类型检查：检查数值型字段类型是否正确，并标记不合格数据")
    parser.add_argument('--input_path', required=True, type=str,
                        help='输入文件路径（支持结构化文件格式：parquet/csv/excel等）')
    parser.add_argument('--output_path', required=True, type=str, help='输出文件路径')
    parser.add_argument('--check_fields_name', required=True, type=str, help='检查字段名，逗号分隔（示例：field1,field2）')
    parser.add_argument('--qc_mark', required=True, type=str, help='质控标识（示例：QC8）')
    parser.add_argument('--mark_field_name', required=True, type=str, default="QC0000",
                        help='质控标识字段名（默认：QC0000）')
    # 可选参数：支持指定输出文件格式（如csv需要指定分隔符）
    parser.add_argument('--sep', type=str, default=',', help='输出CSV文件的分隔符（默认：,）')
    parser.add_argument('--index', action='store_true', default=False, help='是否输出索引列（默认：False）')

    # 解析参数
    args = parser.parse_args()

    try:
        # 1. 读取输入数据
        print(f"Reading input data: {args.input_path}")
        input_df = read_structured_data(args.input_path)

        # 2. 初始化处理器并执行检查
        processor = QC8_DataTypeCheck.from_cli_args(args)
        print(f"Starting data type check, check fields: {args.check_fields_name}")
        output_df = processor.perform(input_df)

        # 3. 写入输出数据
        print(f"Writing output data: {args.output_path}")
        write_structured_data(
            df=output_df,
            output_path=args.output_path,
            sep=args.sep,
            index=args.index
        )
        print("Processing completed!")

    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise e


if __name__ == "__main__":
    main()