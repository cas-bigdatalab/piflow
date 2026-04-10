import argparse
import json
import os

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.aggregator import EntityAttributeAggregator
from data_juicer.utils.constant import Fields, BatchMetaKeys, MetaKeys


class EntityAttributeAggregatorOp:
    """
    EntityAttributeAggregator算子封装类
    从文档中提取并总结给定实体的特定属性
    """

    def __init__(self,
                 api_model: str,
                 entity: str,
                 attribute: str,
                 input_key: str = None,
                 output_key: str = None,
                 word_limit: int = 100,
                 max_token_num: int = None,
                 api_endpoint: str = None,
                 example_prompt: str = None):
        self.api_model = api_model
        self.entity = entity
        self.attribute = attribute
        self.input_key = input_key or MetaKeys.event_description
        self.output_key = output_key or BatchMetaKeys.entity_attribute
        self.word_limit = word_limit
        self.max_token_num = max_token_num
        self.api_endpoint = api_endpoint
        self.example_prompt = example_prompt

    def perform(self, input_path: str, output_path: str):
        """
        执行实体属性聚合操作

        :param input_path: 输入JSON文件路径
        :param output_path: 输出JSON文件路径
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                input_data = json.load(f)

            op_params = {
                'api_model': self.api_model,
                'entity': self.entity,
                'attribute': self.attribute,
                'input_key': self.input_key,
                'output_key': self.output_key,
                'word_limit': self.word_limit,
            }

            if self.max_token_num is not None:
                op_params['max_token_num'] = self.max_token_num
            if self.api_endpoint is not None:
                op_params['api_endpoint'] = self.api_endpoint
            if self.example_prompt is not None:
                op_params['example_prompt'] = self.example_prompt

            op = EntityAttributeAggregator(**op_params)

            if isinstance(input_data, dict) and 'meta' in input_data:
                samples = [input_data]
            elif isinstance(input_data, list):
                samples = input_data
            else:
                raise ValueError("输入JSON格式错误，需要包含 'meta' 字段的字典或文档列表")

            dataset = Dataset.from_list(samples)
            new_dataset = op.run(dataset)

            result = {}
            for i, data in enumerate(new_dataset):
                batch_meta = data.get(Fields.batch_meta, {})
                if self.output_key in batch_meta:
                    if len(new_dataset) == 1:
                        result[self.output_key] = batch_meta[self.output_key]
                    else:
                        result[f'sample_{i}'] = {
                            self.output_key: batch_meta[self.output_key]
                        }

            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"[OK] Entity attribute aggregation completed!")
            print(f"   Entity: {self.entity}")
            print(f"   Attribute: {self.attribute}")
            print(f"   Input file: {input_path}")
            print(f"   Output file: {output_path}")

        except FileNotFoundError:
            print(f"[ERROR] Input file not found: {input_path}")
            raise
        except Exception as e:
            print(f"[ERROR] Error during processing: {str(e)}")
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Entity Attribute Aggregator - 从文档中提取并总结给定实体的特定属性"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--api_model', required=True, type=str,
                        help='API模型名称 (如 qwen2.5-72b-instruct, gpt-4o)')
    parser.add_argument('--entity', required=True, type=str,
                        help='要提取属性的实体名称')
    parser.add_argument('--attribute', required=True, type=str,
                        help='要提取的属性名称 (如 身份背景, 主要经历)')
    parser.add_argument('--input_key', type=str, default=None,
                        help='输入文档的键名 (默认: event_description)')
    parser.add_argument('--output_key', type=str, default=None,
                        help='输出结果的键名 (默认: entity_attribute)')
    parser.add_argument('--word_limit', type=int, default=100,
                        help='输出字数限制 (默认: 100)')
    parser.add_argument('--max_token_num', type=int, default=None,
                        help='输入文档的最大token数 (可选)')
    parser.add_argument('--api_endpoint', type=str, default=None,
                        help='API端点URL (可选)')
    parser.add_argument('--example_prompt', type=str, default=None,
                        help='示例提示词 (可选)')

    args = parser.parse_args()

    aggregator = EntityAttributeAggregatorOp(
        api_model=args.api_model,
        entity=args.entity,
        attribute=args.attribute,
        input_key=args.input_key,
        output_key=args.output_key,
        word_limit=args.word_limit,
        max_token_num=args.max_token_num,
        api_endpoint=args.api_endpoint,
        example_prompt=args.example_prompt
    )

    aggregator.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
