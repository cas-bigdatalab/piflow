import argparse
import pandas as pd
from typing import List
from data_io import read_structured_data, write_structured_data  # 导入data_io工具


class QC11_FieldNullValueCheck:
    """
    字段是否空值检查（需输入检查字段）
    """

    def __init__(self, check_fields_name: str, qc_mark: str, mark_field_name: str, id_field_name: str):
        self.check_fields_name = check_fields_name  # 空值检查字段，多个以逗号分隔
        self.qc_mark = qc_mark  # 质控标识
        self.mark_field_name = mark_field_name  # 质控标识字段名
        self.id_field_name = id_field_name  # 唯一ID字段名

    def perform(self, input_path: str, output_path: str):
        """
        核心处理逻辑：读取数据、空值检查、更新质控标识、输出结果
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        """
        # 1. 读取输入数据
        origin_df = read_structured_data(input_path)

        # 2. 解析需要检查的字段列表
        check_fields = [field.strip() for field in self.check_fields_name.split(',') if field.strip()]
        if not check_fields:
            raise ValueError("检查字段不能为空，请指定需要检查空值的字段")

        # 3. 检查指定字段是否存在空值，生成空值标记
        # 构建空值判断条件：任意指定字段为空则标记为"存在空值"
        origin_df['nullValueFlag'] = origin_df[check_fields].isnull().any(axis=1).map(
            lambda x: '存在空值' if x else '无空值')

        # 4. 筛选出存在空值的异常数据，更新质控标识字段
        abnormal_df = origin_df[origin_df['nullValueFlag'] == '存在空值'].copy()
        if not abnormal_df.empty:
            # 删除原有质控标识字段，新增带当前质控标识的字段
            if self.mark_field_name in abnormal_df.columns:
                abnormal_df = abnormal_df.drop(columns=[self.mark_field_name])
            abnormal_df[self.mark_field_name] = self.qc_mark

        # 5. 合并原始数据和异常数据的质控标识
        # 先删除临时标记列
        origin_df = origin_df.drop(columns=['nullValueFlag'])

        # 按唯一ID关联，更新质控标识
        # 初始化质控标识字段（如果不存在）
        if self.mark_field_name not in origin_df.columns:
            origin_df[self.mark_field_name] = ""

        # 关联异常数据的质控标识
        merge_df = origin_df.merge(
            abnormal_df[[self.id_field_name, self.mark_field_name]],
            on=self.id_field_name,
            how='left',
            suffixes=('', '_new')
        )

        # 合并质控标识（原有标识 + 新标识，用分号分隔，去除开头分号）
        def merge_qc_mark(row):
            original_mark = row[self.mark_field_name] if pd.notna(row[self.mark_field_name]) else ""
            new_mark = row[f'{self.mark_field_name}_new'] if pd.notna(row[f'{self.mark_field_name}_new']) else ""
            merged = f"{original_mark};{new_mark}".strip(';')
            return merged if merged else ""

        merge_df[self.mark_field_name] = merge_df.apply(merge_qc_mark, axis=1)
        # 删除临时列
        merge_df = merge_df.drop(columns=[f'{self.mark_field_name}_new'], errors='ignore')

        # 6. 写入输出文件
        write_structured_data(merge_df, output_path)
        print(
            f"Null value check completed! Processed {len(origin_df)} records, abnormal records: {len(abnormal_df)}, output to: {output_path}")


def main():
    """
    命令行调用入口：支持指定输入输出路径及各项参数
    调用示例：
    python QC11_FieldNullValueCheck.py \
        --input_path /path/to/input.csv \
        --output_path /path/to/output.csv \
        --check_fields_name "field1,field2,field3" \
        --qc_mark "缺测检查" \
        --mark_field_name "QC0000" \
        --id_field_name "ID0000"
    """
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="字段空值检查工具 - 检查指定字段是否存在空值并更新质控标识")

    # 添加参数
    parser.add_argument('--input_path', required=True, type=str, help='输入文件路径（支持结构化文件：csv/parquet等）')
    parser.add_argument('--output_path', required=True, type=str, help='输出文件路径（支持结构化文件：csv/parquet等）')
    parser.add_argument('--check_fields_name', required=True, type=str,
                        help='空值检查字段，多个字段以逗号分隔（示例：field1,field2）')
    parser.add_argument('--qc_mark', default='缺测检查', type=str, help='质控标识（默认：缺测检查）')
    parser.add_argument('--mark_field_name', default='QC0000', type=str, help='质控标识字段名（默认：QC0000）')
    parser.add_argument('--id_field_name', default='ID0000', type=str, help='唯一ID字段名（默认：ID0000）')

    # 解析参数
    args = parser.parse_args()

    # 初始化检查类并执行处理
    checker = QC11_FieldNullValueCheck(
        check_fields_name=args.check_fields_name,
        qc_mark=args.qc_mark,
        mark_field_name=args.mark_field_name,
        id_field_name=args.id_field_name
    )

    # 执行核心逻辑
    try:
        checker.perform(input_path=args.input_path, output_path=args.output_path)
        print("Script executed successfully!")
    except Exception as e:
        print(f"Script execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()