import argparse
import pandas as pd
# 假设data_io.py与当前脚本在同一目录下，需确保该文件存在且包含指定方法
from data_io import read_structured_data, write_structured_data


class FormatConsistency:
    """
    格式一致性校验：数据表结构须与标准化数据模式结构相一致。
    校验方法: 将被检验表的数据表结构与标准化数据模式结构进行比对。
    备注：表头必须完全一致（字段名、字段数量）
    """

    def __init__(self):
        self.description = (
            "格式一致性:数据表结构须与标准化数据模式结构相一致。\n"
            "校验方法:将被检验表的数据表结构与标准化数据模式结构进行比对。\n"
            "备注：表头必须完全一致（字段名、字段数量）"
        )

    def perform(self, original_file_path: str, standard_file_path: str) -> pd.DataFrame:
        """
        核心校验逻辑：比对被检验表和标准表的表头结构
        :param original_file_path: 被检验表的文件路径
        :param standard_file_path: 标准化数据模式表的文件路径
        :return: 校验通过则返回被检验表的DataFrame，校验失败则抛出异常
        """
        # 读取被检验表和标准表
        original_df = read_structured_data(original_file_path)
        standard_df = read_structured_data(standard_file_path)

        # 获取表头字段列表
        original_columns = original_df.columns.tolist()
        standard_columns = standard_df.columns.tolist()

        # 校验字段数量是否一致
        if len(original_columns) != len(standard_columns):
            error_msg = "########## Exception: 一致性检查异常：输入的数据表结构与标准化数据模式结构的字段数目不一致！！！"
            print(error_msg)
            raise Exception(error_msg)

        # 校验字段名称和顺序是否一致
        mismatch_fields = []
        for ori_col, std_col in zip(original_columns, standard_columns):
            if ori_col != std_col:
                mismatch_fields.append(f"{ori_col}:{std_col}")

        # 存在字段不匹配则抛出异常
        if mismatch_fields:
            error_prefix = "########## Exception: 输入的数据表结构与标准化数据模式结构，以下字段未对应："
            print(error_prefix)
            for field in mismatch_fields:
                print(field)
            raise Exception("########## Exception: 一致性检查异常：输入的数据表结构与标准化数据模式结构不一致！！！ ")

        # 校验通过，返回被检验表
        return original_df


def main():
    """
    主函数：接收命令行参数，执行格式一致性校验，并输出结果
    命令行调用示例：
    python format_consistency.py --original_path ./original_data.csv --standard_path ./standard_schema.csv --output_path ./result.csv
    """
    # 初始化参数解析器
    parser = argparse.ArgumentParser(description="格式一致性校验工具")
    # 添加命令行参数
    parser.add_argument(
        "--original_path",
        type=str,
        required=True,
        help="被检验数据表的文件路径（如：./data/original.csv）"
    )
    parser.add_argument(
        "--standard_path",
        type=str,
        required=True,
        help="标准化数据模式表的文件路径（如：./data/standard.csv）"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="校验通过后的数据输出路径（如：./data/result.csv）"
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 初始化校验类并执行校验
    checker = FormatConsistency()
    try:
        # 执行核心校验逻辑
        result_df = checker.perform(args.original_path, args.standard_path)
        # 写入输出文件
        write_structured_data(result_df, args.output_path)
        print("Format consistency check passed! Data output to:", args.output_path)
    except Exception as e:
        print(f"Check failed: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()