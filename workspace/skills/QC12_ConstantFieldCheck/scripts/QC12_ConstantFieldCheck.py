import argparse
import pandas as pd
from typing import List
# 假设data_io.py在同级目录，需确保该文件存在且包含指定方法
from data_io import read_structured_data, write_structured_data


class QC12_ConstantFieldCheck:
    """
    特定字段恒定下的其他字段不一致检查
    """

    def __init__(self, constant_fields_names: str, diff_fields_names: str,
                 qc_mark: str, mark_field_name: str, id_field_name: str):
        # 初始化参数
        self.constant_fields = [field.strip() for field in constant_fields_names.split(',')]
        self.diff_fields = [field.strip() for field in diff_fields_names.split(',')]
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name
        self.id_field_name = id_field_name

    def perform(self, input_path: str, output_path: str):
        """
        核心处理逻辑
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        """
        # 1. 读取输入数据
        origin_df = read_structured_data(input_path)

        # 校验必要字段是否存在
        self._validate_fields(origin_df)

        # 2. 找出恒定字段分组下，差异字段存在多个不同值的分组
        # 分组并检查每个分组内差异字段的唯一值数量是否>1
        grouped = origin_df.groupby(self.constant_fields)
        # 筛选出有差异的分组的恒定字段组合
        diff_groups = []
        for name, group in grouped:
            has_diff = False
            for diff_field in self.diff_fields:
                if group[diff_field].nunique() > 1:
                    has_diff = True
                    break
            if has_diff:
                # 将分组名（元组）转为字典，方便后续匹配
                group_dict = dict(zip(self.constant_fields, name)) if isinstance(name, tuple) else {
                    self.constant_fields[0]: name}
                diff_groups.append(group_dict)

        # 3. 找出所有属于差异分组的异常数据行
        if diff_groups:
            # 构建筛选条件
            filter_cond = pd.Series([False] * len(origin_df))
            for group in diff_groups:
                cond = pd.Series([True] * len(origin_df))
                for field, value in group.items():
                    cond = cond & (origin_df[field] == value)
                filter_cond = filter_cond | cond
            abnormal_df = origin_df[filter_cond].copy()
        else:
            abnormal_df = pd.DataFrame(columns=origin_df.columns)

        # 4. 处理质控标识字段
        # 移除原有标识字段（如果存在），添加新标识
        if self.mark_field_name in abnormal_df.columns:
            abnormal_df = abnormal_df.drop(columns=[self.mark_field_name])
        abnormal_df[self.mark_field_name] = self.qc_mark

        # 5. 合并原始数据和异常数据，更新质控标识
        # 先确保原始数据有质控标识字段
        if self.mark_field_name not in origin_df.columns:
            origin_df[self.mark_field_name] = ""

        # 左连接原始数据和异常数据（基于唯一ID）
        merged_df = origin_df.merge(
            abnormal_df[[self.id_field_name, self.mark_field_name]],
            on=self.id_field_name,
            how='left',
            suffixes=('', '_abnormal')
        )

        # 拼接质控标识，处理空值和开头的分号
        def concat_qc_mark(row):
            original_mark = row[self.mark_field_name] if pd.notna(row[self.mark_field_name]) else ""
            abnormal_mark = row[f"{self.mark_field_name}_abnormal"] if pd.notna(
                row[f"{self.mark_field_name}_abnormal"]) else ""
            combined = f"{original_mark};{abnormal_mark}".strip(';')
            return combined if combined else ""

        merged_df[self.mark_field_name] = merged_df.apply(concat_qc_mark, axis=1)
        # 移除临时列
        merged_df = merged_df.drop(columns=[f"{self.mark_field_name}_abnormal"], errors='ignore')

        # 6. 写入输出文件
        write_structured_data(merged_df, output_path)

    def _validate_fields(self, df: pd.DataFrame):
        """
        校验数据中是否包含必要字段
        """
        all_required_fields = self.constant_fields + self.diff_fields + [self.id_field_name]
        missing_fields = [field for field in all_required_fields if field not in df.columns]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def main():
    """
    命令行调用入口
    示例调用指令：
    python QC12_ConstantFieldCheck.py \
        --input_path "/path/to/input.csv" \
        --output_path "/path/to/output.csv" \
        --constantFieldsNames "field1,field2" \
        --diffFieldsNames "field3,field4" \
        --QcMark "QC12" \
        --markFieldName "QC0000" \
        --idFieldName "ID0000"
    """
    # 构建命令行参数解析器
    parser = argparse.ArgumentParser(description="特定字段恒定下的其他字段不一致检查")

    # 添加参数
    parser.add_argument('--input_path', required=True, help="输入文件路径")
    parser.add_argument('--output_path', required=True, help="输出文件路径")
    parser.add_argument('--constantFieldsNames', required=True, help="恒定字段（按照此字段进行分组），多个字段用逗号分隔")
    parser.add_argument('--diffFieldsNames', required=True, help="存在不一致的字段，多个字段用逗号分隔")
    parser.add_argument('--QcMark', required=True, help="质控标识")
    parser.add_argument('--markFieldName', default="QC0000", help="质控标识字段名，默认值：QC0000")
    parser.add_argument('--idFieldName', default="ID0000", help="唯一ID字段名，默认值：ID0000")

    # 解析参数
    args = parser.parse_args()

    # 初始化处理类并执行
    checker = QC12_ConstantFieldCheck(
        constant_fields_names=args.constantFieldsNames,
        diff_fields_names=args.diffFieldsNames,
        qc_mark=args.QcMark,
        mark_field_name=args.markFieldName,
        id_field_name=args.idFieldName
    )

    # 执行核心逻辑
    try:
        checker.perform(args.input_path, args.output_path)
        print(f"Processing completed! Output saved to: {args.output_path}")
    except Exception as e:
        print(f"Processing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()