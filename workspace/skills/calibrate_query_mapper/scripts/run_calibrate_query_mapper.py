import argparse
import json
from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.mapper.calibrate_query_mapper import CalibrateQueryMapper


def run_calibrate_query_mapper(
    input_path: str,
    output_path: str,
    api_model: str,
    api_endpoint: str = None,
    response_path: str = None,
):
    """
    Calibrate Query Mapper - 基于参考文本校准问答对中的查询

    参照测试代码 test_calibrate_query_mapper.py 中的 _run_op 函数实现：
    1. 初始化算子（必须指定api_model）
    2. 将数据转为Dataset，使用 op.run(dataset) 处理

    参数:
        input_path: 输入JSON文件路径
        output_path: 输出JSON文件路径
        api_model: LLM模型名称（必需）
        api_endpoint: API端点URL（可选）
        response_path: 响应内容路径（可选）
    """
    # 读取输入文件
    with open(input_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # 初始化算子
    op_params = {
        "api_model": api_model,
    }
    if api_endpoint:
        op_params["api_endpoint"] = api_endpoint
    if response_path:
        op_params["response_path"] = response_path

    op = CalibrateQueryMapper(**op_params)

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
    parser = argparse.ArgumentParser(
        description="Calibrate Query Mapper - 基于参考文本校准问答对中的查询"
    )
    parser.add_argument(
        "--input_path", type=str, required=True, help="输入JSON文件路径"
    )
    parser.add_argument(
        "--output_path", type=str, required=True, help="输出JSON文件路径"
    )
    parser.add_argument("--api_model", type=str, required=True, help="LLM模型名称")
    parser.add_argument("--api_endpoint", type=str, default=None, help="API端点URL")
    parser.add_argument("--response_path", type=str, default=None, help="响应内容路径")

    args = parser.parse_args()
    run_calibrate_query_mapper(
        args.input_path,
        args.output_path,
        args.api_model,
        args.api_endpoint,
        args.response_path,
    )
