import argparse
import pandas as pd
from typing import Dict, List, Any
from data_io import read_structured_data, write_structured_data


class QC6_SingleFieldMultiThresholdCheck:
    """
    单字段多条件阈值检验：将被检验表中的指定字段的属性项值与阈值表比对，检查是否在门限范围，
    不允许超出门限值（包括上限和下限）（阈值表的结构必须包括 'min_value' ,'max_value'）
    """

    def __init__(self, field_name: str, qc_mark: str, mark_field_name: str, id_field_name: str):
        self.field_name = field_name
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name
        self.id_field_name = id_field_name

    def perform(self, original_file_path: str, threshold_file_path: str,
                origin_output_path: str, error_output_path: str = None):
        """
        核心处理逻辑
        :param original_file_path: 原始数据文件路径
        :param threshold_file_path: 阈值表文件路径
        :param origin_output_path: 处理后原始数据输出路径
        :param error_output_path: 异常数据输出路径（可选）
        """
        # 读取原始表和阈值表
        origin_df = read_structured_data(original_file_path)
        multi_threshold_df = read_structured_data(threshold_file_path)

        # 构建阈值判断逻辑
        def check_threshold(row):
            """逐行判断是否符合阈值条件"""
            for _, threshold_row in multi_threshold_df.iterrows():
                match = True
                for col in multi_threshold_df.columns:
                    col_val = threshold_row[col]
                    if col.startswith("max"):
                        if pd.isna(row[self.field_name]) or row[self.field_name] > float(col_val):
                            match = False
                            break
                    elif col.startswith("min"):
                        if pd.isna(row[self.field_name]) or row[self.field_name] < float(col_val):
                            match = False
                            break
                    else:
                        if str(row[col]) != str(col_val):
                            match = False
                            break
                if match:
                    return 0
            return 1

        # 添加flag列标记异常数据
        origin_df['flag'] = origin_df.apply(check_threshold, axis=1)

        # 筛选异常数据
        abnormal_df = origin_df[origin_df['flag'] == 1].drop('flag', axis=1)
        # 更新异常数据的质控标识字段
        if self.mark_field_name in abnormal_df.columns:
            abnormal_df = abnormal_df.drop(self.mark_field_name, axis=1)
        abnormal_df[self.mark_field_name] = self.qc_mark

        # 构建输出数据的字段列表（排除质控标识字段）
        output_fields = [col for col in origin_df.columns if col != self.mark_field_name and col != 'flag']

        # 合并原始数据和异常数据，更新质控标识
        origin_df = origin_df.drop('flag', axis=1)
        # 左连接异常数据
        merged_df = pd.merge(
            origin_df,
            abnormal_df[[self.id_field_name, self.mark_field_name]],
            on=self.id_field_name,
            how='left',
            suffixes=('', '_abnormal')
        )

        # 处理质控标识拼接
        def concat_qc_mark(row):
            mark_list = [row[self.mark_field_name],
                         self.qc_mark if pd.notna(row[f'{self.mark_field_name}_abnormal']) else None]
            mark_list = [m for m in mark_list if m is not None and m != '']
            merged_mark = ';'.join(mark_list).lstrip(';')
            return merged_mark if merged_mark else ''

        merged_df[self.mark_field_name] = merged_df.apply(concat_qc_mark, axis=1)
        # 删除临时列，保留最终输出字段
        merged_df = merged_df[output_fields + [self.mark_field_name]]

        # 输出处理后的数据
        write_structured_data(merged_df, origin_output_path)

        # 可选：输出异常数据
        if error_output_path and not abnormal_df.empty:
            # 按ID排序输出
            abnormal_df_sorted = abnormal_df.sort_values(by=self.id_field_name)
            write_structured_data(abnormal_df_sorted, error_output_path)

        # 打印异常信息（可选）
        if not abnormal_df.empty:
            print("########## Exception: Threshold check failed: out of range!!!")
            print(f"First 10 abnormal records:")
            print(abnormal_df.head(10))


def main():
    """
    命令行调用入口，支持指定输入输出路径和必要参数
    示例调用：
    python QC6_SingleFieldMultiThresholdCheck.py \
        --original_file ./data/original.csv \
        --threshold_file ./data/threshold.csv \
        --origin_output ./data/processed_origin.csv \
        --error_output ./data/error_data.csv \
        --field_name temperature \
        --qc_mark QC6_001 \
        --mark_field_name QC_MARK \
        --id_field_name ID
    """
    parser = argparse.ArgumentParser(description='单字段多条件阈值检验工具')

    # 文件路径参数
    parser.add_argument('--original_file', required=True, help='原始数据文件路径')
    parser.add_argument('--threshold_file', required=True, help='阈值表文件路径')
    parser.add_argument('--origin_output', required=True, help='处理后原始数据输出路径')
    parser.add_argument('--error_output', help='异常数据输出路径（可选）')

    # 核心参数
    parser.add_argument('--field_name', required=True, help='阈值检查字段名')
    parser.add_argument('--qc_mark', required=True, help='质控标识（如QC6_001）')
    parser.add_argument('--mark_field_name', required=True, default='QC0000',
                        help='质控标识字段名（默认QC0000）')
    parser.add_argument('--id_field_name', required=True, default='ID0000',
                        help='唯一ID字段名（默认ID0000）')

    # 解析参数
    args = parser.parse_args()

    # 初始化并执行检验逻辑
    qc_checker = QC6_SingleFieldMultiThresholdCheck(
        field_name=args.field_name,
        qc_mark=args.qc_mark,
        mark_field_name=args.mark_field_name,
        id_field_name=args.id_field_name
    )

    # 执行处理
    qc_checker.perform(
        original_file_path=args.original_file,
        threshold_file_path=args.threshold_file,
        origin_output_path=args.origin_output,
        error_output_path=args.error_output
    )


if __name__ == '__main__':
    main()