import argparse
import pandas as pd
# 导入 data_io 模块中的数据读写方法
from data_io import read_structured_data, write_structured_data


class QC3_NumericDataThresholdCheck:
    """数值数据阈值检验：将被检验表中的属性项值与门限比对，检查是否在门限范围，不允许超出门限值之外"""

    def __init__(self, field_name: str, max_value: str, min_value: str,
                 additional_condition: str = "1 == 1", qc_mark: str = "",
                 mark_field_name: str = "QC0000", id_field_name: str = "ID0000"):
        """
        初始化阈值检验参数
        :param field_name: 阈值检测字段
        :param max_value: 最大值
        :param min_value: 最小值
        :param additional_condition: 额外查询条件（SQL 风格，如 "type=1"）
        :param qc_mark: 质控标识
        :param mark_field_name: 质控标识字段名
        :param id_field_name: 唯一ID字段名
        """
        self.field_name = field_name
        self.max_value = float(max_value)
        self.min_value = float(min_value)
        self.additional_condition = additional_condition if additional_condition else "1 == 1"
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name
        self.id_field_name = id_field_name

    def perform(self, input_path: str, origin_output_path: str, error_output_path: str = None):
        """
        执行阈值检验逻辑
        :param input_path: 输入文件路径
        :param origin_output_path: 处理后原始数据输出路径（标记质控结果）
        :param error_output_path: 异常数据输出路径（可选）
        """
        # 1. 读取输入数据
        origin_df = read_structured_data(input_path)

        # 2. 校验字段是否存在
        if self.field_name not in origin_df.columns:
            raise ValueError(f"检测字段 {self.field_name} 不存在于输入数据中！")
        if self.id_field_name not in origin_df.columns:
            raise ValueError(f"唯一ID字段 {self.id_field_name} 不存在于输入数据中！")

        # 3. 确保检测字段为数值类型
        origin_df[self.field_name] = pd.to_numeric(origin_df[self.field_name], errors='coerce')

        # 4. 构建筛选条件（先处理额外条件，再处理阈值条件）
        # 4.1 处理额外条件（使用 pandas query 语法）
        try:
            if self.additional_condition.strip() == "1 == 1":
                filtered_df = origin_df
            else:
                filtered_df = origin_df.query(self.additional_condition)
        except Exception as e:
            raise ValueError(f"额外条件解析失败：{self.additional_condition}，错误信息：{str(e)}")

        # 4.2 筛选阈值异常数据
        threshold_condition = (filtered_df[self.field_name] > self.max_value) | (
                    filtered_df[self.field_name] < self.min_value)
        abnormal_df = filtered_df[threshold_condition].copy()

        # 5. 标记异常数据的质控字段
        if self.mark_field_name not in origin_df.columns:
            origin_df[self.mark_field_name] = ""
        if not abnormal_df.empty:
            # 为异常数据添加质控标记
            abnormal_df[self.mark_field_name] = self.qc_mark
            # 左连接，更新原始数据的质控标记
            origin_df = origin_df.merge(
                abnormal_df[[self.id_field_name, self.mark_field_name]],
                on=self.id_field_name,
                how='left',
                suffixes=('', '_new')
            )
            # 合并质控标记（处理原有标记 + 新标记）
            origin_df[self.mark_field_name] = origin_df.apply(
                lambda row: ';'.join(filter(None, [row[self.mark_field_name], row[f'{self.mark_field_name}_new']])),
                axis=1
            )
            # 删除临时列
            origin_df = origin_df.drop(columns=[f'{self.mark_field_name}_new'])

        # 6. 输出数据
        # 输出标记后的原始数据
        write_structured_data(origin_df, origin_output_path)
        # 可选：输出异常数据
        if error_output_path and not abnormal_df.empty:
            write_structured_data(abnormal_df, error_output_path)

        # 打印异常信息（可选）
        if not abnormal_df.empty:
            print("########## Exception: 阈值检测异常：阈值超限！！！")
            print(f"异常数据条数：{len(abnormal_df)}")
            print("前10条异常数据：")
            print(abnormal_df.head(10))


def main():
    """
    命令行调用入口：支持通过 python 指令传递参数并执行脚本
    示例调用：
    python QC3_NumericDataThresholdCheck.py \
        --input_path /path/to/input.csv \
        --origin_output_path /path/to/output_origin.csv \
        --error_output_path /path/to/output_error.csv \
        --field_name temperature \
        --max_value 100 \
        --min_value 0 \
        --additional_condition "region='north'" \
        --qc_mark QC3_THRESHOLD_ERROR \
        --mark_field_name QC0000 \
        --id_field_name ID0000
    """
    # 构建命令行参数解析器
    parser = argparse.ArgumentParser(description="数值数据阈值检验脚本")
    # 必选：文件路径参数
    parser.add_argument("--input_path", required=True, type=str, help="输入文件路径")
    parser.add_argument("--origin_output_path", required=True, type=str, help="标记后原始数据输出路径")
    parser.add_argument("--error_output_path", type=str, default=None, help="异常数据输出路径（可选）")
    # 必选：阈值检验参数
    parser.add_argument("--field_name", required=True, type=str, help="阈值检测字段")
    parser.add_argument("--max_value", required=True, type=str, help="最大值")
    parser.add_argument("--min_value", required=True, type=str, help="最小值")
    # 可选参数
    parser.add_argument("--additional_condition", type=str, default="1 == 1", help="额外查询条件（如 type==1）")
    parser.add_argument("--qc_mark", required=True, type=str, help="质控标识")
    parser.add_argument("--mark_field_name", type=str, default="QC0000", help="质控标识字段名")
    parser.add_argument("--id_field_name", type=str, default="ID0000", help="唯一ID字段名")

    # 解析参数
    args = parser.parse_args()

    # 初始化检验类并执行
    checker = QC3_NumericDataThresholdCheck(
        field_name=args.field_name,
        max_value=args.max_value,
        min_value=args.min_value,
        additional_condition=args.additional_condition,
        qc_mark=args.qc_mark,
        mark_field_name=args.mark_field_name,
        id_field_name=args.id_field_name
    )
    checker.perform(
        input_path=args.input_path,
        origin_output_path=args.origin_output_path,
        error_output_path=args.error_output_path
    )


if __name__ == "__main__":
    main()