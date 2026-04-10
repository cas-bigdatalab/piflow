import argparse
import pandas as pd
# 假设data_io是自定义的结构化文件读写工具，read_structured_data/write_structured_data
from data_io import read_structured_data, write_structured_data


class DC3_RoundOff:
    """四舍五入数据处理类"""
    description = "四舍五入"

    def __init__(self, flow_name: str = "", file_name: str = ""):
        self.flow_name = flow_name
        self.file_name = file_name

    def perform(self, input_origin_path: str, input_standard_path: str, output_path: str):
        """
        核心处理逻辑：读取原始数据和标准配置数据，按配置对数字型字段进行四舍五入
        :param input_origin_path: 原始数据文件输入路径
        :param input_standard_path: 标准配置文件输入路径
        :param output_path: 处理后数据输出路径
        """
        # 1. 读取输入文件（通过data_io工具）
        origin_df = read_structured_data(input_origin_path)
        standard_df = read_structured_data(input_standard_path)

        # 2. 过滤标准配置数据（仅保留指定流水线和文件的配置）
        if self.flow_name and self.file_name:
            standard_df = standard_df[
                (standard_df["流水线"] == self.flow_name) &
                (standard_df["表名"] == self.file_name)
            ]

        # 3. 筛选数字型字段的四舍五入配置（字段代码、小数位）
        num_config_df = standard_df[standard_df["字段类型"] == "数字型"][["字段代码", "小数位"]]
        num_config_df.rename(columns={"字段代码": "name", "小数位": "num"}, inplace=True)
        # 确保小数位为整数类型
        num_config_df["num"] = num_config_df["num"].astype(int)

        # 4. 构建字段处理映射
        field_round_config = dict(zip(num_config_df["name"], num_config_df["num"]))

        # 5. 对原始数据进行四舍五入处理
        processed_df = origin_df.copy()
        for col in processed_df.columns:
            if col in field_round_config:
                decimal_place = field_round_config[col]
                # 仅对数值型字段执行四舍五入
                if pd.api.types.is_numeric_dtype(processed_df[col]):
                    processed_df[col] = processed_df[col].round(decimal_place)

        # 6. 输出处理后的数据（通过data_io工具）
        write_structured_data(processed_df, output_path)
        print(f"Round off completed, result saved to: {output_path}")


def main():
    """
    命令行调用入口：
    示例调用指令：
    python dc3_round_off.py --origin_path ./origin_data.csv --standard_path ./standard_config.csv --output_path ./result.csv --flow_name 测试流水线 --file_name 测试文件.csv
    """
    # 构建命令行参数解析器
    parser = argparse.ArgumentParser(description=DC3_RoundOff.description)
    # 必选参数：文件输入输出路径
    parser.add_argument("--origin_path", required=True, help="原始数据文件输入路径")
    parser.add_argument("--standard_path", required=True, help="标准配置文件输入路径")
    parser.add_argument("--output_path", required=True, help="处理后数据输出路径")
    # 可选参数：流水线名称、文件名称
    parser.add_argument("--flow_name", default="", help="流水线名称")
    parser.add_argument("--file_name", default="", help="流水线内要处理的文件名称")

    # 解析命令行参数
    args = parser.parse_args()

    # 初始化处理类并执行核心逻辑
    round_off_processor = DC3_RoundOff(
        flow_name=args.flow_name,
        file_name=args.file_name
    )
    round_off_processor.perform(
        input_origin_path=args.origin_path,
        input_standard_path=args.standard_path,
        output_path=args.output_path
    )


if __name__ == "__main__":
    main()