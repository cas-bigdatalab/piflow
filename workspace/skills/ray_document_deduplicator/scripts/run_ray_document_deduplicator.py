import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.deduplicator.ray_document_deduplicator import RayDocumentDeduplicator


class RayDocumentDeduplicatorOp:
    """
    RayDocumentDeduplicator算子封装类
    使用Ray分布式框架在文档级别删除重复样本
    """

    def __init__(self,
                 lowercase: bool = False,
                 ignore_non_character: bool = False,
                 backend: str = 'ray_actor',
                 redis_address: str = 'redis://localhost:6379',
                 text_key: str = 'text'):
        self.lowercase = lowercase
        self.ignore_non_character = ignore_non_character
        self.backend = backend
        self.redis_address = redis_address
        self.text_key = text_key

    def perform(self, input_path: str, output_path: str):
        """
        执行文档去重操作

        :param input_path: 输入JSON文件路径
        :param output_path: 输出JSON文件路径
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        if isinstance(input_data, dict) and 'data' in input_data:
            samples = input_data['data']
        elif isinstance(input_data, list):
            samples = input_data
        else:
            raise ValueError("输入JSON格式错误，需要包含 'data' 字段的字典或文档列表")

        dataset = Dataset.from_list(samples)

        op = RayDocumentDeduplicator(
            lowercase=self.lowercase,
            ignore_non_character=self.ignore_non_character,
            backend=self.backend,
            redis_address=self.redis_address
        )

        dataset = dataset.map(op.calculate_hash)
        dataset, _ = op.process(dataset)
        dataset = dataset.select_columns(column_names=[self.text_key])

        res_list = dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_list, f, ensure_ascii=False, indent=2)

        original_count = len(samples)
        deduplicated_count = len(res_list)
        removed_count = original_count - deduplicated_count

        print(f"[OK] Ray document deduplication completed!")
        print(f"   Backend: {self.backend}")
        print(f"   Original documents: {original_count}")
        print(f"   Deduplicated documents: {deduplicated_count}")
        print(f"   Removed duplicates: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="RayDocumentDeduplicator - 使用Ray分布式框架在文档级别删除重复样本"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--lowercase', type=lambda x: x.lower() == 'true', default=False,
                        help='是否将文本转为小写进行比对 (默认: False)')
    parser.add_argument('--ignore_non_character', type=lambda x: x.lower() == 'true', default=False,
                        help='是否忽略非字母字符进行比对 (默认: False)')
    parser.add_argument('--backend', type=str, default='ray_actor',
                        choices=['ray_actor', 'redis'],
                        help='分布式后端 (默认: ray_actor)')
    parser.add_argument('--redis_address', type=str, default='redis://localhost:6379',
                        help='Redis地址 (默认: redis://localhost:6379)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='文本字段的键名 (默认: text)')

    args = parser.parse_args()

    deduplicator = RayDocumentDeduplicatorOp(
        lowercase=args.lowercase,
        ignore_non_character=args.ignore_non_character,
        backend=args.backend,
        redis_address=args.redis_address,
        text_key=args.text_key
    )

    deduplicator.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
