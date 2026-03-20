import argparse
from data_io import read_structured_data, write_structured_data


def space_cleaning(input_path: str, output_path: str):
    """
    检查字符串类型的字段前后是否有空格，如有空格则删除
    :param input_path: 输入文件路径（适配data_io支持的所有格式）
    :param output_path: 输出文件路径（适配data_io支持的所有格式）
    """
    # 使用data_io读取结构化数据
    df = read_structured_data(input_path)

    # 遍历所有字符串类型列，去除前后空格（对齐Scala原逻辑）
    for col in df.columns:
        # 匹配Scala中StringType的字段处理逻辑
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()

    # 使用data_io写入清理后的数据
    write_structured_data(df, output_path)

    print(f"Space cleaning completed, saved to: {output_path}")


def main():
    """
    命令行调用入口，支持指定输入输出路径
    调用示例：
    python DC2_SpaceCleaning.py --input_path ./input.csv --output_path ./output.csv
    """
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='字符串字段前后空格清理工具（适配data_io结构化读写）')
    parser.add_argument('--input_path', required=True, type=str, help='输入文件路径')
    parser.add_argument('--output_path', required=True, type=str, help='输出文件路径')

    # 解析参数
    args = parser.parse_args()

    # 执行空格清理逻辑
    try:
        space_cleaning(args.input_path, args.output_path)
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise


if __name__ == '__main__':
    main()