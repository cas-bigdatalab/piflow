import argparse
import pandas as pd
# 假设data_io.py在当前目录或已加入环境变量，需确保该模块可导入
from data_io import read_structured_data, write_structured_data


class AddMonotonicallyIncreasingID:
    """添加单调递增ID，如果字段存在则不添加"""

    def __init__(self, id_field_name: str = "ID0000"):
        self.id_field_name = id_field_name

    def process(self, input_path: str, output_path: str):
        """
        核心处理逻辑：读取数据、添加自增ID、写入结果
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        """
        # 1. 读取结构化数据
        df = read_structured_data(input_path)

        # 2. 核心逻辑：判断字段是否存在，不存在则添加自增ID
        if self.id_field_name not in df.columns:
            # 添加从1开始的单调递增ID
            df[self.id_field_name] = range(1, len(df) + 1)
            # 调整字段顺序：把ID字段放到第一列
            cols = [self.id_field_name] + [col for col in df.columns if col != self.id_field_name]
            df = df[cols]

        # 3. 写入处理后的数据
        write_structured_data(df, output_path)


def main():
    """
    主函数：接收命令行参数，执行ID添加逻辑
    调用示例：
    python add_monotonic_id.py --input_path ./input.csv --output_path ./output.csv --id_field_name ID0000
    """
    # 初始化命令行参数解析器
    parser = argparse.ArgumentParser(description="添加单调递增ID，如果字段存在则不添加")
    # 添加必要参数
    parser.add_argument("--input_path", required=True, type=str, help="输入文件路径（支持结构化文件格式：csv/parquet等）")
    parser.add_argument("--output_path", required=True, type=str, help="输出文件路径")
    parser.add_argument("--id_field_name", default="ID0000", type=str,
                        help="自增ID字段名称（默认：ID0000）")

    # 解析参数
    args = parser.parse_args()

    # 初始化处理器并执行处理逻辑
    processor = AddMonotonicallyIncreasingID(id_field_name=args.id_field_name)
    processor.process(input_path=args.input_path, output_path=args.output_path)

    print(f"Processing completed! Result saved to: {args.output_path}")


if __name__ == "__main__":
    # 直接运行脚本时触发main函数
    main()