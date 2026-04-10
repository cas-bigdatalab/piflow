import argparse

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.deduplicator.document_deduplicator import DocumentDeduplicator
from data_io import read_file, write_file


class DocumentDeduplicatorOp:
    """
    DocumentDeduplicator算子封装类
    使用精确匹配在文档级别删除重复的样本
    """

    def __init__(self,
                 lowercase: bool = False,
                 ignore_non_character: bool = False,
                 text_key: str = 'text'):
        self.lowercase = lowercase
        self.ignore_non_character = ignore_non_character
        self.text_key = text_key

    def perform(self, input_path: str, output_path: str):
        """
        执行文档去重操作

        :param input_path: 输入文件路径 (支持 json, txt)
        :param output_path: 输出文件路径 (支持 json, txt)
        """
        samples = read_file(input_path, self.text_key)

        dataset = Dataset.from_list(samples)

        op = DocumentDeduplicator(
            lowercase=self.lowercase,
            ignore_non_character=self.ignore_non_character
        )

        dataset = dataset.map(op.compute_hash)
        dataset, _ = op.process(dataset)

        res_list = dataset.to_list()

        write_file(res_list, output_path)

        original_count = len(samples)
        deduplicated_count = len(res_list)
        removed_count = original_count - deduplicated_count

        print(f"[OK] Document deduplication completed!")
        print(f"   Original documents: {original_count}")
        print(f"   Deduplicated documents: {deduplicated_count}")
        print(f"   Removed duplicates: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="DocumentDeduplicator - 使用精确匹配在文档级别删除重复样本"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径 (支持 json, txt)')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径 (支持 json, txt)')
    parser.add_argument('--lowercase', type=lambda x: x.lower() == 'true', default=False,
                        help='是否将文本转为小写进行比对 (默认: False)')
    parser.add_argument('--ignore_non_character', type=lambda x: x.lower() == 'true', default=False,
                        help='是否忽略非字母字符进行比对 (默认: False)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='文本字段的键名 (默认: text)')

    args = parser.parse_args()

    deduplicator = DocumentDeduplicatorOp(
        lowercase=args.lowercase,
        ignore_non_character=args.ignore_non_character,
        text_key=args.text_key
    )

    deduplicator.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
