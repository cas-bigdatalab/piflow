import argparse
import os
# 导入结构化文件读写工具
from data_io import read_structured_data, write_structured_data


class DC1BlankLineClean:
    """
    空行清洗工具类（对标Scala版本DC1_BlankLineClean）
    功能：读取结构化文件并删除所有空行（所有列均为空的行），输出处理后的文件
    """

    def __init__(self):
        # 对应原Scala代码中的description
        self.description = "空行清洗，如有空行删除"

    def perform(self, input_path: str, output_path: str):
        """
        核心处理逻辑：读取文件、删除空行、输出文件
        :param input_path: 输入文件路径（支持read_structured_data的所有格式）
        :param output_path: 输出文件路径（支持write_structured_data的所有格式）
        """
        try:
            # 1. 通过结构化读写工具读取文件（替代原输入流）
            df = read_structured_data(input_path)

            # 2. 空行清洗：删除所有列都为空的行（对标Scala的df.na.drop("all")）
            cleaned_df = df.dropna(how='all')

            # 3. 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 4. 通过结构化读写工具写入文件（替代原输出流）
            write_structured_data(cleaned_df, output_path)

            print(f"[OK] Blank line cleaning completed!")
            print(f"   输入文件：{input_path}")
            print(f"   输出文件：{output_path}")
            print(f"   清洗前行数：{len(df)} | 清洗后行数：{len(cleaned_df)}")

        except FileNotFoundError:
            print(f"❌ 错误：输入文件 {input_path} 不存在！")
            raise
        except Exception as e:
            print(f"❌ 处理过程中发生错误：{str(e)}")
            raise


def main():
    """
    命令行调用入口（支持用户通过python指令指定输入输出路径）
    调用示例：
    python DC1_BlankLineClean.py --input ./input.csv --output ./output.csv
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="空行清洗工具 - 对标Scala版本DC1_BlankLineClean")

    # 添加必填参数：输入/输出路径
    parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="输入文件路径（支持csv/excel/json等，与read_structured_data兼容）"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="输出文件路径（支持csv/excel/json等，与write_structured_data兼容）"
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 执行清洗逻辑
    cleaner = DC1BlankLineClean()
    cleaner.perform(input_path=args.input, output_path=args.output)


# 脚本直接运行时触发main函数
if __name__ == "__main__":
    main()