import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.aggregator import MetaTagsAggregator
from data_juicer.utils.constant import Fields, MetaKeys


class MetaTagsAggregatorOp:
    """
    MetaTagsAggregator算子封装类
    合并相似的元标签
    """

    def __init__(self,
                 api_model: str,
                 meta_tag_key: str,
                 target_tags: str = None,
                 api_endpoint: str = None):
        self.api_model = api_model
        self.meta_tag_key = meta_tag_key
        self.target_tags = target_tags.split(',') if target_tags else None
        self.api_endpoint = api_endpoint

    def perform(self, input_path: str, output_path: str):
        """
        执行元标签聚合操作

        :param input_path: 输入JSON文件路径
        :param output_path: 输出JSON文件路径
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            samples = json.load(f)

        if not isinstance(samples, list):
            samples = [samples]

        dataset = Dataset.from_list(samples)

        op_params = {
            'api_model': self.api_model,
            'meta_tag_key': self.meta_tag_key,
        }

        if self.target_tags:
            op_params['target_tags'] = self.target_tags
        if self.api_endpoint:
            op_params['api_endpoint'] = self.api_endpoint

        op = MetaTagsAggregator(**op_params)
        new_dataset = op.run(dataset)

        result = new_dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[OK] Meta tags aggregation completed!")
        print(f"   API model: {self.api_model}")
        print(f"   Meta tag key: {self.meta_tag_key}")
        if self.target_tags:
            print(f"   Target tags: {self.target_tags}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="MetaTagsAggregator - 合并相似的元标签"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--api_model', required=True, type=str,
                        help='API模型名称 (如 qwen2.5-72b-instruct, gpt-4o)')
    parser.add_argument('--meta_tag_key', required=True, type=str,
                        help='元数据标签的键名 (如 query_sentiment_label)')
    parser.add_argument('--target_tags', type=str, default=None,
                        help='目标标签列表，逗号分隔 (如 开心,难过,其他)')
    parser.add_argument('--api_endpoint', type=str, default=None,
                        help='API端点URL (可选)')

    args = parser.parse_args()

    aggregator = MetaTagsAggregatorOp(
        api_model=args.api_model,
        meta_tag_key=args.meta_tag_key,
        target_tags=args.target_tags,
        api_endpoint=args.api_endpoint
    )

    aggregator.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
