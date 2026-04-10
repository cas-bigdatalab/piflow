import argparse
import pandas as pd
from typing import Optional
# 假设data_io.py在当前目录或已加入Python路径
from data_io import read_structured_data, write_structured_data


class QC4_AssociationRuleCheck:
    """
    数值关联规则校验，具有关联关系数据项满足特定约束条件（该组件支持用户根据类似hive sql规则自定义条件）
    """
    def __init__(self, expression: str, filter_type: str, qc_mark: str, mark_field_name: str, id_field_name: str):
        """
        初始化校验类
        :param expression: where条件表达式（类似hive sql的where条件）
        :param filter_type: yes/not，yes表示满足表达式的是正确数据，not表示满足表达式的是异常数据
        :param qc_mark: 质控标识字符串
        :param mark_field_name: 质控标识字段名
        :param id_field_name: 唯一ID字段名
        """
        self.expression = expression
        self.filter_type = filter_type
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name
        self.id_field_name = id_field_name

    def _eval_expression(self, df: pd.DataFrame) -> pd.Series:
        """
        解析并执行where条件表达式，返回布尔筛选序列
        注：pandas的eval语法与hive sql有部分差异，需保证expression符合pandas.eval规范
        :param df: 原始DataFrame
        :return: 布尔筛选序列
        """
        try:
            # 使用pandas eval执行表达式，生成布尔索引
            return df.eval(self.expression)
        except Exception as e:
            raise ValueError(f"Expression parse failed: {self.expression}, error: {str(e)}")

    def process(self, input_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        核心处理逻辑
        :param input_df: 输入DataFrame
        :return: (处理后的原始数据DF, 异常数据DF)
        """
        # 1. 校验必要字段存在
        if self.id_field_name not in input_df.columns:
            raise ValueError(f"ID field {self.id_field_name} not found in input data")
        if self.mark_field_name not in input_df.columns:
            # 如果质控标识字段不存在，先创建空字段
            input_df = input_df.copy()
            input_df[self.mark_field_name] = ""

        # 2. 执行表达式筛选数据
        filter_mask = self._eval_expression(input_df)
        abnormal_df = input_df[filter_mask].copy()

        # 3. 根据filter_type调整异常数据（yes表示满足表达式的是正确数据，需要取反）
        if self.filter_type == "yes":
            abnormal_df = input_df[~filter_mask].copy()

        # 4. 处理质控标识字段
        if self.mark_field_name in abnormal_df.columns:
            abnormal_df = abnormal_df.drop(columns=[self.mark_field_name])
        abnormal_df[self.mark_field_name] = self.qc_mark

        # 5. 合并原始数据和异常数据的质控标识
        # 先创建用于join的临时列（避免索引问题）
        input_df_temp = input_df.copy().reset_index(drop=True)
        abnormal_df_temp = abnormal_df.copy().reset_index(drop=True)

        # 左连接获取异常标记
        merged_df = input_df_temp.merge(
            abnormal_df_temp[[self.id_field_name, self.mark_field_name]],
            on=self.id_field_name,
            how="left",
            suffixes=("", "_abnormal")
        )

        # 拼接质控标识
        def concat_qc_mark(original, abnormal):
            if pd.isna(abnormal):
                return original.strip(";") if pd.notna(original) else ""
            combined = f"{original};{abnormal}" if pd.notna(original) else abnormal
            return combined.lstrip(";")

        merged_df[self.mark_field_name] = merged_df.apply(
            lambda row: concat_qc_mark(row[self.mark_field_name], row[f"{self.mark_field_name}_abnormal"]),
            axis=1
        )

        # 移除临时列，恢复原始结构
        merged_df = merged_df.drop(columns=[f"{self.mark_field_name}_abnormal"], errors="ignore")

        # 6. 排序异常数据（按ID）
        abnormal_df = abnormal_df.sort_values(by=self.id_field_name).reset_index(drop=True)

        return merged_df, abnormal_df

    def run(self, input_path: str, origin_output_path: str, error_output_path: Optional[str] = None):
        """
        执行完整流程：读取数据 -> 处理 -> 输出结果
        :param input_path: 输入文件路径
        :param origin_output_path: 处理后原始数据输出路径
        :param error_output_path: 异常数据输出路径（可选）
        """
        # 1. 读取输入数据
        print(f"Reading input data: {input_path}")
        input_df = read_structured_data(input_path)

        # 2. 核心处理
        print("Starting numeric association rule check...")
        origin_df, error_df = self.process(input_df)

        # 3. 输出处理后的数据
        print(f"Writing processed data: {origin_output_path}")
        write_structured_data(origin_df, origin_output_path)

        # 4. 输出异常数据（如果指定路径）
        if error_output_path:
            print(f"Writing error data: {error_output_path}")
            write_structured_data(error_df, error_output_path)

        # 5. 打印异常数据预览（如果有）
        if not error_df.empty:
            print("=" * 50)
            print(f"Found {len(error_df)} abnormal records, first 10 preview:")
            print(error_df.head(10))
            print("=" * 50)
        else:
            print("No abnormal data found")


def main():
    """
    命令行调用入口函数
    示例调用：
    python QC4_AssociationRuleCheck.py \
        --input_path ./input_data.parquet \
        --origin_output_path ./output/origin_data.parquet \
        --error_output_path ./output/error_data.parquet \
        --expression "age < 0 or age > 120" \
        --filter_type not \
        --qc_mark "QC4_AGE_INVALID" \
        --mark_field_name QC0000 \
        --id_field_name ID0000
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="数值关联规则校验工具")

    # 文件路径参数
    parser.add_argument("--input_path", required=True, type=str, help="输入文件路径")
    parser.add_argument("--origin_output_path", required=True, type=str, help="处理后原始数据输出路径")
    parser.add_argument("--error_output_path", type=str, default=None, help="异常数据输出路径（可选）")

    # 业务参数
    parser.add_argument("--expression", required=True, type=str,
                        help="""where条件表达式（pandas eval语法），示例：
                        1：关系运算(==,!=,<,<=,>,>=,isna, notna, str.contains)
                        2：逻辑运算(&,|,~)
                        3：数值运算(round,abs,sin,cos)
                        4：字符串函数(str.len, str.lower, str.upper, str.strip)
                        5：数学运算(+, -, *, /, %)
                        6：类型转换: astype，例：age.astype('float')
                        """)
    parser.add_argument("--filter_type", required=True, type=str, choices=["yes", "not"],
                        help="yes：满足表达式的是正确数据；not：满足表达式的是异常数据")
    parser.add_argument("--qc_mark", required=True, type=str, help="质控标识字符串")
    parser.add_argument("--mark_field_name", required=True, type=str, default="QC0000",
                        help="质控标识字段名（默认：QC0000）")
    parser.add_argument("--id_field_name", required=True, type=str, default="ID0000",
                        help="唯一ID字段名（默认：ID0000）")

    # 解析参数
    args = parser.parse_args()

    # 初始化并执行校验
    qc_checker = QC4_AssociationRuleCheck(
        expression=args.expression,
        filter_type=args.filter_type,
        qc_mark=args.qc_mark,
        mark_field_name=args.mark_field_name,
        id_field_name=args.id_field_name
    )

    # 执行处理流程
    qc_checker.run(
        input_path=args.input_path,
        origin_output_path=args.origin_output_path,
        error_output_path=args.error_output_path
    )


if __name__ == "__main__":
    main()