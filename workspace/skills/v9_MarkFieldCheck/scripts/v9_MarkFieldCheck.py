import argparse
import pandas as pd
# 导入data_io模块中的结构化数据读写方法
from data_io import read_structured_data, write_structured_data


class MarkFieldCheck:
    """
    标识符字段检查：判断是否存在质量标识符字段，如果没有，则添加
    """

    def __init__(self, mark_field_name: str = "QC0000"):
        self.mark_field_name = mark_field_name

    def perform(self, input_path: str, output_path: str):
        """
        核心处理逻辑：读取数据 -> 检查并添加标识字段 -> 输出数据
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        """
        # 1. 使用data_io读取结构化数据
        df = read_structured_data(input_path)

        # 2. 核心逻辑：检查字段是否存在，不存在则添加空字符串列（模拟原逻辑的null string类型）
        if self.mark_field_name not in df.columns:
            df[self.mark_field_name] = pd.NA  # 使用pandas的缺失值标识，对应原逻辑的null

        # 3. 使用data_io写入结构化数据
        write_structured_data(df, output_path)


def main():
    """
    主函数：解析命令行参数，实例化并执行检查逻辑
    支持通过Python命令行调用，指定输入/输出路径和标识字段名
    """
    # 初始化参数解析器
    parser = argparse.ArgumentParser(description="标识符字段检查工具：判断是否存在质量标识符字段，不存在则添加")

    # 添加命令行参数
    parser.add_argument(
        "--input_path",
        type=str,
        required=True,
        help="输入结构化文件的路径（如csv/parquet等）"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="输出结构化文件的路径"
    )
    parser.add_argument(
        "--mark_field_name",
        type=str,
        default="QC0000",
        help="质量标识字段名（默认值：QC0000）"
    )

    # 解析参数
    args = parser.parse_args()

    # 实例化并执行检查逻辑
    checker = MarkFieldCheck(mark_field_name=args.mark_field_name)
    checker.perform(input_path=args.input_path, output_path=args.output_path)

    print(f"Processing completed! Output file saved to: {args.output_path}")


if __name__ == "__main__":
    # 当脚本被直接调用时执行主函数
    main()