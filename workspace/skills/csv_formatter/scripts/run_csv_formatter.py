import argparse
import json
import os

from data_juicer.format.csv_formatter import CsvFormatter

_COMMON_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1', 'cp1252']


def run_csv_formatter(input_path: str,
                      output_path: str,
                      text_keys: list = None,
                      add_suffix: bool = False,
                      num_proc: int = 1,
                      encoding: str = 'utf-8'):
    """
    运行CSV格式化算子

    :param input_path: 输入CSV文件路径或目录
    :param output_path: 输出JSONL文件路径
    :param text_keys: 文本字段名列表（不传则不进行空文本过滤）
    :param add_suffix: 是否添加文件后缀信息
    :param num_proc: 并行进程数
    :param encoding: CSV文件编码（不传则自动尝试常见编码）
    """
    # 构建编码尝试列表
    encodings_to_try = [encoding]
    for enc in _COMMON_ENCODINGS:
        if enc not in encodings_to_try:
            encodings_to_try.append(enc)

    last_error = None
    dataset = None
    for enc in encodings_to_try:
        try:
            formatter = CsvFormatter(
                dataset_path=input_path,
                text_keys=text_keys,
                add_suffix=add_suffix,
                encoding=enc,
            )
            dataset = formatter.load_dataset(num_proc=num_proc)
            if enc != encoding:
                print(f"指定编码 {encoding} 读取失败，使用编码 {enc} 读取成功")
            break
        except Exception as e:
            last_error = e
            continue

    if dataset is None:
        raise RuntimeError(
            f"无法读取文件，已尝试编码: {encodings_to_try}，最后错误: {last_error}"
        )

    # 保存为 JSONL 格式
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in dataset.to_list():
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: 共 {len(dataset)} 条数据")
    print(f"结果已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='CSV格式化器 - 加载和格式化CSV类型的文件'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入CSV文件路径或目录')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出JSONL文件路径')
    parser.add_argument('--text_keys', type=str, action='append', default=None,
                        help='文本字段名，可重复指定多个 (默认: text)')
    parser.add_argument('--add_suffix', action='store_true',
                        help='是否添加文件后缀信息')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')
    parser.add_argument('--encoding', type=str, default='utf-8',
                        help='CSV文件编码 (默认: utf-8)')

    args = parser.parse_args()

    run_csv_formatter(
        input_path=args.input_path,
        output_path=args.output_path,
        text_keys=args.text_keys,
        add_suffix=args.add_suffix,
        num_proc=args.num_proc,
        encoding=args.encoding
    )


if __name__ == '__main__':
    main()