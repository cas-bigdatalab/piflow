import argparse
import pandas as pd
# 导入data_io工具中的结构化文件读写方法
from data_io import read_structured_data, write_structured_data


class DataSorting:
    """数据排序类，实现指定字段的升序/降序排序"""

    def __init__(self, id_field_name: str, sort_order: str = "asc"):
        """
        初始化排序参数
        :param id_field_name: 排序字段名（支持多个字段，用逗号分隔）
        :param sort_order: 排序方式，可选值：asc(升序)/desc(降序)
        """
        self.id_field_name = id_field_name
        # 校验排序方式合法性
        if sort_order not in ["asc", "desc"]:
            raise ValueError(f"排序方式{sort_order}不合法，仅支持asc/desc")
        self.sort_order = sort_order

    def perform(self, input_path: str, output_path: str):
        """
        核心处理逻辑：读取数据 -> 排序 -> 输出数据
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        """
        # 1. 读取结构化数据（依赖data_io）
        df = read_structured_data(input_path)

        # 2. 解析排序字段（支持多字段，按逗号分割）
        sort_fields = [field.strip() for field in self.id_field_name.split(",")]
        # 校验排序字段是否存在于数据中
        missing_fields = [field for field in sort_fields if field not in df.columns]
        if missing_fields:
            raise ValueError(f"数据中缺失排序字段：{missing_fields}")

        # 3. 执行排序
        ascending = True if self.sort_order == "asc" else False
        sorted_df = df.sort_values(by=sort_fields, ascending=ascending)

        # 4. 写入结构化数据（依赖data_io）
        write_structured_data(sorted_df, output_path)
        print(f"Data sorting completed! Output to: {output_path}")


def main():
    """
    主函数：支持命令行参数调用，示例：
    python data_sorting.py --input_path ./input.csv --output_path ./output.csv --id_field_name "ID0000" --sort_order asc
    """
    # 初始化命令行参数解析器
    parser = argparse.ArgumentParser(description="数据排序脚本 - 支持指定字段升/降序排序")
    # 添加必选参数
    parser.add_argument("--input_path", type=str, required=True, help="输入文件路径（结构化文件，如csv/parquet等）")
    parser.add_argument("--output_path", type=str, required=True, help="输出文件路径")
    parser.add_argument("--id_field_name", type=str, required=True, help="排序字段名（多字段用逗号分隔，如：ID0000,NAME）")
    parser.add_argument("--sort_order", type=str, default="asc", choices=["asc", "desc"], help="排序方式（默认asc升序，可选desc降序）")

    # 解析参数
    args = parser.parse_args()

    # 初始化排序类并执行处理
    try:
        sorter = DataSorting(
            id_field_name=args.id_field_name,
            sort_order=args.sort_order
        )
        sorter.perform(
            input_path=args.input_path,
            output_path=args.output_path
        )
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    # 脚本直接运行时调用main函数
    main()