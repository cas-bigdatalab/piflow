import argparse
import json
from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.mapper.chinese_convert_mapper import ChineseConvertMapper


def run_chinese_convert_mapper(input_path: str, output_path: str, mode: str = "s2t"):
    """
    Chinese Convert Mapper - 在繁体中文、简体中文和日语汉字之间转换中文

    参照测试代码 test_chinese_convert_mapper.py 中的 _run_chinese_convert 函数实现：
    1. 初始化算子（指定mode）
    2. 将数据转为Dataset，使用 op.run(dataset) 处理

    参数:
        input_path: 输入JSON文件路径
        output_path: 输出JSON文件路径
        mode: 转换模式，默认 's2t'
    """
    # 读取输入文件
    with open(input_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # 初始化算子
    op = ChineseConvertMapper(mode=mode)

    # 将数据转为Dataset，使用run方法处理
    dataset = Dataset.from_list(samples)
    result_dataset = op.run(dataset)

    # 转换为列表并保存
    result_list = [dict(sample) for sample in result_dataset]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=2)

    print(f"处理完成：{len(samples)} 条样本，模式：{mode}")
    print(f"输出文件：{output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chinese Convert Mapper - 中文繁简转换"
    )
    parser.add_argument(
        "--input_path", type=str, required=True, help="输入JSON文件路径"
    )
    parser.add_argument(
        "--output_path", type=str, required=True, help="输出JSON文件路径"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="s2t",
        help="转换模式 (s2t, t2s, s2tw, tw2s, s2hk, hk2s, s2twp, tw2sp, t2tw, tw2t, hk2t, t2hk, t2jp, jp2t)",
    )

    args = parser.parse_args()
    run_chinese_convert_mapper(args.input_path, args.output_path, args.mode)
