import argparse
import json
import os
import re
import csv
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')


class FormatDetector:
    """
    采集基础格式识别工具类
    对接入资源进行格式预识别，判断文本、表格、文档、图像等类型
    并为后续流程分配对应处理路径
    """

    TEXT_EXTENSIONS = {'.txt', '.md', '.rst', '.log', '.text'}
    TABLE_EXTENSIONS = {'.csv', '.tsv', '.xlsx', '.xls'}
    PDF_EXTENSIONS = {'.pdf'}
    DOCUMENT_EXTENSIONS = {'.doc'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}
    DATA_EXTENSIONS = {'.json', '.jsonl', '.xml', '.yaml', '.yml'}
    HTML_EXTENSIONS = {'.html', '.htm'}

    CATEGORY_ROUTE = {
        'text': 'text_collector',
        'table': 'table_collector',
        'pdf': 'pdf_collector',
        'document': 'manual_review',
        'image': 'image_collector',
        'data': 'content_parser',
        'html': 'content_parser',
        'unknown': 'manual_review'
    }

    def __init__(
        self,
        recursive: bool = False,
        output_format: str = 'jsonl',
        group_by_type: bool = False
    ):
        self.recursive = recursive
        self.output_format = output_format
        self.group_by_type = group_by_type

    def _detect_file_category(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.TEXT_EXTENSIONS:
            return 'text'
        if ext in self.TABLE_EXTENSIONS:
            return 'table'
        if ext in self.PDF_EXTENSIONS:
            return 'pdf'
        if ext in self.DOCUMENT_EXTENSIONS:
            return 'document'
        if ext in self.IMAGE_EXTENSIONS:
            return 'image'
        if ext in self.DATA_EXTENSIONS:
            return 'data'
        if ext in self.HTML_EXTENSIONS:
            return 'html'
        return 'unknown'

    def _detect_content_format(self, file_path: str) -> str:
        """对文本类文件进一步检测内容格式"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.TABLE_EXTENSIONS | self.IMAGE_EXTENSIONS | self.DOCUMENT_EXTENSIONS | self.DATA_EXTENSIONS | self.HTML_EXTENSIONS:
            return ext.lstrip('.')
        encodings = ['utf-8', 'gbk', 'latin-1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    sample = f.read(512)
                if re.search(r'<[a-zA-Z][^>]*>', sample):
                    return 'html'
                if re.search(r'^#{1,6}\s', sample, re.MULTILINE):
                    return 'markdown'
                if sample.strip().startswith('{') or sample.strip().startswith('['):
                    return 'json'
                return 'plain_text'
            except (UnicodeDecodeError, LookupError):
                continue
        return 'binary'

    def _collect_files(self, input_path: str) -> list:
        files = []
        if os.path.isfile(input_path):
            files.append(input_path)
        elif os.path.isdir(input_path):
            walk = os.walk(input_path) if self.recursive else [(input_path, [], os.listdir(input_path))]
            for root, _, filenames in walk:
                for fname in filenames:
                    fp = os.path.join(root, fname)
                    if os.path.isfile(fp):
                        files.append(fp)
        else:
            raise FileNotFoundError(f"输入路径不存在: {input_path}")
        return sorted(files)

    def _write_output(self, records: list, output_path: str):
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        fmt = self.output_format
        if fmt == 'auto':
            ext = os.path.splitext(output_path)[1].lower()
            fmt = {'.json': 'json', '.csv': 'csv'}.get(ext, 'jsonl')

        if fmt == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        elif fmt == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        elif fmt == 'csv':
            if records:
                with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)

    def perform(self, input_path: str, output_path: str) -> dict:
        files = self._collect_files(input_path)
        total = len(files)
        if total == 0:
            raise ValueError(f"输入路径下未找到任何文件")

        records = []
        category_counts = {}

        for fp in files:
            stat = os.stat(fp)
            category = self._detect_file_category(fp)
            content_format = self._detect_content_format(fp)
            route = self.CATEGORY_ROUTE.get(category, 'manual_review')
            category_counts[category] = category_counts.get(category, 0) + 1

            if os.path.isfile(input_path):
                file_path = os.path.basename(fp)
            else:
                file_path = os.path.relpath(fp, input_path).replace(os.sep, '/')

            record = {
                'file_path': file_path,
                'filename': os.path.basename(fp),
                'extension': os.path.splitext(fp)[1].lower(),
                'category': category,
                'content_format': content_format,
                'recommended_route': route,
                'file_size': stat.st_size,
                'detected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            records.append(record)

        self._write_output(records, output_path)

        print(f"\n[OK] Format detection completed!")
        print(f"   Input path: {input_path}")
        print(f"   Total files: {total}")
        print(f"   Category distribution:")
        for cat, cnt in sorted(category_counts.items()):
            print(f"     - {cat}: {cnt} files -> {self.CATEGORY_ROUTE.get(cat, 'manual_review')}")
        print(f"   Output: {output_path}")

        return {'total': total, 'categories': category_counts}


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', '1', 'yes'):
        return True
    elif value.lower() in ('false', '0', 'no'):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def main():
    parser = argparse.ArgumentParser(
        description="FormatDetector - 采集基础格式识别工具"
    )
    parser.add_argument('--input', required=True, type=str,
                        help='输入文件或目录路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径（格式识别结果）')
    parser.add_argument('--recursive', type=str_to_bool, default=False,
                        help='是否递归处理子目录，默认false')
    parser.add_argument('--output_format', type=str, default='jsonl',
                        choices=['jsonl', 'json', 'csv', 'auto'],
                        help='输出格式，默认jsonl')

    args = parser.parse_args()

    detector = FormatDetector(
        recursive=args.recursive,
        output_format=args.output_format
    )
    detector.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
