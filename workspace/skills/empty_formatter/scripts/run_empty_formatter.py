import argparse
import json
import os

from data_juicer.format.empty_formatter import EmptyFormatter


def run_empty_formatter(output_path: str,
                       length: int = 0,
                       feature_keys: list = None):
    """
    运行空数据格式化算子

    :param output_path: 输出JSONL文件路径
    :param length: 空数据集长度
    :param feature_keys: 字段名列表
    """
    # 处理 feature_keys 参数
    if feature_keys is None:
        feature_keys = []

    # 初始化格式化器
    formatter = EmptyFormatter(
        length=length,
        feature_keys=feature_keys
    )

    # 加载数据集
    dataset = formatter.load_dataset()

    # 保存为 JSONL 格式
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in dataset.to_list():
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: 创建 {len(dataset)} 条空数据")
    print(f"结果已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='空数据格式化器 - 创建空数据集'
    )
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出JSONL文件路径')
    parser.add_argument('--length', type=int, default=0,
                        help='空数据集长度 (默认: 0)')
    parser.add_argument('--feature_keys', type=str, action='append', default=None,
                        help='字段名，可重复指定多个')

    args = parser.parse_args()

    run_empty_formatter(
        output_path=args.output_path,
        length=args.length,
        feature_keys=args.feature_keys
    )


if __name__ == '__main__':
    main()