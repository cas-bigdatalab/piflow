import argparse
import json
import os
import csv
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')


class TableCollector:
    """
    表格类数据采集接入工具类
    适配CSV、TSV、Excel等结构化表格科研数据的采集接入
    """

    SUPPORTED_EXTENSIONS = ['.csv', '.tsv', '.xlsx', '.xls']
    COMMON_ENCODINGS = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    def __init__(
        self,
        encoding: str = 'auto',
        recursive: bool = False,
        add_metadata: bool = True,
        output_format: str = 'jsonl'
    ):
        self.encoding = encoding
        self.recursive = recursive
        self.add_metadata = add_metadata
        self.output_format = output_format

    def _detect_encoding(self, file_path: str) -> str:
        for enc in self.COMMON_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    f.read(512)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue
        return 'utf-8'

    def _read_csv(self, file_path: str, delimiter: str = ',') -> list:
        enc = self.encoding if self.encoding != 'auto' else self._detect_encoding(file_path)
        rows = []
        with open(file_path, 'r', encoding=enc, newline='', errors='replace') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                rows.append(dict(row))
        return rows

    def _read_excel(self, file_path: str) -> list:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return []
            headers = [str(h) if h is not None else f'col_{i}' for i, h in enumerate(rows[0])]
            result = []
            for row in rows[1:]:
                record = {}
                for h, v in zip(headers, row):
                    record[h] = str(v) if v is not None else ''
                result.append(record)
            wb.close()
            return result
        except ImportError:
            raise ImportError("读取Excel文件需要安装openpyxl: pip install openpyxl")

    def _collect_files(self, input_path: str) -> list:
        files = []
        if os.path.isfile(input_path):
            files.append(input_path)
        elif os.path.isdir(input_path):
            walk = os.walk(input_path) if self.recursive else [(input_path, [], os.listdir(input_path))]
            for root, _, filenames in walk:
                for fname in filenames:
                    if os.path.splitext(fname)[1].lower() in self.SUPPORTED_EXTENSIONS:
                        files.append(os.path.join(root, fname))
        else:
            raise FileNotFoundError(f"输入路径不存在: {input_path}")
        return sorted(files)

    def _read_table_file(self, file_path: str) -> list:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return self._read_csv(file_path, delimiter=',')
        elif ext == '.tsv':
            return self._read_csv(file_path, delimiter='\t')
        elif ext in ['.xlsx', '.xls']:
            return self._read_excel(file_path)
        return []

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
        total_files = len(files)
        if total_files == 0:
            raise ValueError(f"未找到支持的表格文件（{self.SUPPORTED_EXTENSIONS}）")

        all_records = []
        skipped_files = 0
        file_stats = []

        for fp in files:
            try:
                rows = self._read_table_file(fp)
                if os.path.isfile(input_path):
                    source_file = os.path.basename(fp)
                else:
                    source_file = os.path.relpath(fp, input_path).replace(os.sep, '/')
                meta = {
                    'source_file': source_file,
                    'filename': os.path.basename(fp),
                    'row_count': len(rows),
                    'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                if self.add_metadata:
                    for row in rows:
                        row['_meta'] = meta
                all_records.extend(rows)
                file_stats.append({'file': os.path.basename(fp), 'rows': len(rows)})
            except Exception as e:
                print(f"[WARN] 读取失败 {fp}: {e}")
                skipped_files += 1

        self._write_output(all_records, output_path)

        print(f"\n[OK] Table collection completed!")
        print(f"   Input path: {input_path}")
        print(f"   Files found: {total_files}")
        print(f"   Files skipped: {skipped_files}")
        print(f"   Total rows collected: {len(all_records)}")
        for fs in file_stats:
            print(f"     - {fs['file']}: {fs['rows']} rows")
        print(f"   Output file: {output_path}")

        return {'total_files': total_files, 'skipped_files': skipped_files, 'total_rows': len(all_records)}


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
        description="TableCollector - 表格类数据采集接入工具"
    )
    parser.add_argument('--input', required=True, type=str,
                        help='输入文件或目录路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--encoding', type=str, default='auto',
                        help='文件编码，默认auto自动检测')
    parser.add_argument('--recursive', type=str_to_bool, default=False,
                        help='是否递归处理子目录，默认false')
    parser.add_argument('--add_metadata', type=str_to_bool, default=True,
                        help='是否添加文件元信息，默认true')
    parser.add_argument('--output_format', type=str, default='jsonl',
                        choices=['jsonl', 'json', 'csv', 'auto'],
                        help='输出格式，默认jsonl')

    args = parser.parse_args()

    collector = TableCollector(
        encoding=args.encoding,
        recursive=args.recursive,
        add_metadata=args.add_metadata,
        output_format=args.output_format
    )
    collector.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
