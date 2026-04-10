import argparse
import json
from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.mapper.clean_links_mapper import CleanLinksMapper


def run_clean_links_mapper(input_path: str, output_path: str, repl: str = ""):
    """
    Clean Links Mapper - 清理文本中的HTTP/HTTPS/FTP链接

    参照测试代码 test_clean_links_mapper.py 中的 _run_clean_links 函数实现：
    1. 初始化算子（可指定 repl 参数）
    2. 将数据转为Dataset，使用 op.run(dataset) 处理

    参数:
        input_path: 输入JSON文件路径
        output_path: 输出JSON文件路径
        repl: 替换字符串，默认为空字符串（即删除）
    """
    # 读取输入文件
    with open(input_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # 初始化算子
    op = CleanLinksMapper(repl=repl)

    # 将数据转为Dataset，使用run方法处理
    dataset = Dataset.from_list(samples)
    result_dataset = op.run(dataset)

    # 转换为列表并保存
    result_list = [dict(sample) for sample in result_dataset]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=2)

    print(f"处理完成：{len(samples)} 条样本")
    print(f"输出文件：{output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean Links Mapper - 清理链接")
    parser.add_argument(
        "--input_path", type=str, required=True, help="输入JSON文件路径"
    )
    parser.add_argument(
        "--output_path", type=str, required=True, help="输出JSON文件路径"
    )
    parser.add_argument(
        "--repl", type=str, default="", help="替换字符串（默认为空，即删除）"
    )

    args = parser.parse_args()
    run_clean_links_mapper(args.input_path, args.output_path, args.repl)
