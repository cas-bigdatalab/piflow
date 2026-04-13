import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.aggregator import MostRelevantEntitiesAggregator
from data_juicer.utils.constant import Fields, BatchMetaKeys, MetaKeys


class MostRelevantEntitiesAggregatorOp:
    """
    MostRelevantEntitiesAggregator算子封装类
    从文档中提取与给定实体最相关的指定类型实体，并按重要性排序
    """

    def __init__(self,
                 api_model: str,
                 entity: str,
                 query_entity_type: str,
                 input_key: str = None,
                 output_key: str = None,
                 max_token_num: int = None,
                 api_endpoint: str = None):
        self.api_model = api_model
        self.entity = entity
        self.query_entity_type = query_entity_type
        self.input_key = input_key or MetaKeys.event_description
        self.output_key = output_key or BatchMetaKeys.most_relevant_entities
        self.max_token_num = max_token_num
        self.api_endpoint = api_endpoint

    def perform(self, input_path: str, output_path: str):
        """
        执行最相关实体聚合操作

        :param input_path: 输入JSON文件路径
        :param output_path: 输出JSON文件路径
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        if isinstance(input_data, dict) and 'meta' in input_data:
            samples = [input_data]
        elif isinstance(input_data, list):
            samples = input_data
        else:
            raise ValueError("输入JSON格式错误，需要包含 'meta' 字段的字典或文档列表")

        dataset = Dataset.from_list(samples)

        op_params = {
            'api_model': self.api_model,
            'entity': self.entity,
            'query_entity_type': self.query_entity_type,
            'input_key': self.input_key,
            'output_key': self.output_key,
        }

        if self.max_token_num:
            op_params['max_token_num'] = self.max_token_num
        if self.api_endpoint:
            op_params['api_endpoint'] = self.api_endpoint

        op = MostRelevantEntitiesAggregator(**op_params)
        new_dataset = op.run(dataset)

        result = []
        for data in new_dataset:
            item = {}
            if Fields.batch_meta in data and self.output_key in data[Fields.batch_meta]:
                item[self.output_key] = list(data[Fields.batch_meta][self.output_key])
            result.append(item)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[OK] Most relevant entities aggregation completed!")
        print(f"   Entity: {self.entity}")
        print(f"   Query entity type: {self.query_entity_type}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="MostRelevantEntitiesAggregator - 提取与给定实体最相关的指定类型实体"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--api_model', required=True, type=str,
                        help='API模型名称 (如 qwen2.5-72b-instruct)')
    parser.add_argument('--entity', required=True, type=str,
                        help='要查询的实体名称')
    parser.add_argument('--query_entity_type', required=True, type=str,
                        help='要查询的相关实体类型 (如 人物、地点、组织)')
    parser.add_argument('--input_key', type=str, default=None,
                        help='输入文档的键名 (默认: event_description)')
    parser.add_argument('--output_key', type=str, default=None,
                        help='输出结果的键名 (默认: most_relevant_entities)')
    parser.add_argument('--max_token_num', type=int, default=None,
                        help='输入文档的最大token数 (可选)')
    parser.add_argument('--api_endpoint', type=str, default=None,
                        help='API端点URL (可选)')

    args = parser.parse_args()

    aggregator = MostRelevantEntitiesAggregatorOp(
        api_model=args.api_model,
        entity=args.entity,
        query_entity_type=args.query_entity_type,
        input_key=args.input_key,
        output_key=args.output_key,
        max_token_num=args.max_token_num,
        api_endpoint=args.api_endpoint
    )

    aggregator.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
