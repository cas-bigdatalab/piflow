import argparse
import json
import os
import re
import csv
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')


class ContentParser:
    """
    接入内容解析预处理工具类
    对采集完成后的原始内容开展轻量解析预处理，提取基础文本、表格结构或元属性信息
    """

    def __init__(
        self,
        parse_mode: str = 'auto',
        extract_title: bool = True,
        extract_paragraphs: bool = True,
        output_format: str = 'jsonl'
    ):
        self.parse_mode = parse_mode
        self.extract_title = extract_title
        self.extract_paragraphs = extract_paragraphs
        self.output_format = output_format

    def _detect_content_type(self, text: str) -> str:
        """自动检测内容类型"""
        if re.search(r'<[a-zA-Z][^>]*>', text):
            return 'html'
        if re.search(r'^#{1,6}\s', text, re.MULTILINE):
            return 'markdown'
        if re.search(r'\\(section|chapter|begin|end)\{', text):
            return 'latex'
        return 'plain'

    def _parse_plain(self, text: str) -> dict:
        """解析纯文本"""
        result = {'raw_text': text, 'content_type': 'plain'}
        lines = text.split('\n')

        if self.extract_title:
            for line in lines[:10]:
                stripped = line.strip()
                if stripped and len(stripped) > 3:
                    result['title'] = stripped
                    break

        if self.extract_paragraphs:
            paragraphs = []
            current = []
            for line in lines:
                if line.strip():
                    current.append(line)
                else:
                    if current:
                        para = ' '.join(current).strip()
                        paragraphs.append(para)
                        current = []
            if current:
                para = ' '.join(current).strip()
                paragraphs.append(para)
            result['paragraphs'] = paragraphs
            result['paragraph_count'] = len(paragraphs)

        return result

    def _parse_markdown(self, text: str) -> dict:
        """解析Markdown"""
        result = {'raw_text': text, 'content_type': 'markdown'}

        if self.extract_title:
            m = re.search(r'^#{1,2}\s+(.+)$', text, re.MULTILINE)
            if m:
                result['title'] = m.group(1).strip()

        if self.extract_paragraphs:
            clean = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
            clean = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', clean)
            clean = re.sub(r'`[^`]*`', '', clean)
            clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
            paragraphs = [p.strip() for p in re.split(r'\n{2,}', clean)
                          if p.strip()]
            result['paragraphs'] = paragraphs
            result['paragraph_count'] = len(paragraphs)

        return result

    def _parse_html(self, text: str) -> dict:
        """解析HTML"""
        result = {'raw_text': text, 'content_type': 'html'}
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, 'html.parser')
            if self.extract_title:
                title_tag = soup.find('title') or soup.find('h1')
                if title_tag:
                    result['title'] = title_tag.get_text(strip=True)
            if self.extract_paragraphs:
                paragraphs = []
                for tag in soup.find_all(['p', 'div', 'section']):
                    t = tag.get_text(separator=' ', strip=True)
                    if t:
                        paragraphs.append(t)
                result['paragraphs'] = paragraphs
                result['paragraph_count'] = len(paragraphs)
        except ImportError:
            clean = re.sub(r'<[^>]+>', ' ', text)
            clean = re.sub(r'\s+', ' ', clean).strip()
            result['text'] = clean
        return result

    def _parse_record(self, record: dict) -> dict:
        """解析单条记录"""
        text = record.get('text', '')
        if text is None or text == '':
            return {**record, '_parsed': {'error': '无文本内容'}}
        if not isinstance(text, str):
            text = str(text)

        mode = self.parse_mode
        if mode == 'auto':
            mode = self._detect_content_type(text)

        if mode == 'markdown':
            parsed = self._parse_markdown(text)
        elif mode == 'html':
            parsed = self._parse_html(text)
        else:
            parsed = self._parse_plain(text)

        parsed['char_count'] = len(text)
        parsed['word_count'] = len(text.split())
        parsed['parsed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        result = {k: v for k, v in record.items() if k != 'text'}
        result['_parsed'] = parsed
        result['text'] = text
        return result

    def _read_input(self, input_path: str) -> list:
        ext = os.path.splitext(input_path)[1].lower()
        records = []
        encodings = ['utf-8', 'gbk', 'latin-1']

        if ext == '.jsonl':
            for enc in encodings:
                try:
                    with open(input_path, 'r', encoding=enc) as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                records.append(json.loads(line))
                    break
                except UnicodeDecodeError:
                    continue
        elif ext == '.json':
            for enc in encodings:
                try:
                    with open(input_path, 'r', encoding=enc) as f:
                        data = json.load(f)
                    records = data if isinstance(data, list) else [data]
                    break
                except UnicodeDecodeError:
                    continue
        elif ext == '.txt':
            for enc in encodings:
                try:
                    with open(input_path, 'r', encoding=enc) as f:
                        records = [{'text': f.read()}]
                    break
                except UnicodeDecodeError:
                    continue
        else:
            raise ValueError(f"不支持的输入格式: {ext}")
        return records

    def _write_output(self, records: list, output_path: str):
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        fmt = self.output_format
        if fmt == 'auto':
            ext = os.path.splitext(output_path)[1].lower()
            fmt = {'.json': 'json'}.get(ext, 'jsonl')

        if fmt == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        elif fmt == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)

    def perform(self, input_path: str, output_path: str) -> dict:
        records = self._read_input(input_path)
        total = len(records)

        parsed_records = []
        failed = 0
        type_counts = {}

        for rec in records:
            try:
                result = self._parse_record(rec)
                ct = result.get('_parsed', {}).get('content_type', 'unknown')
                type_counts[ct] = type_counts.get(ct, 0) + 1
                parsed_records.append(result)
            except Exception as e:
                print(f"[WARN] 解析失败: {e}")
                failed += 1
                parsed_records.append(rec)

        self._write_output(parsed_records, output_path)

        print(f"\n[OK] Content parsing completed!")
        print(f"   Input: {input_path}")
        print(f"   Total records: {total}")
        print(f"   Parsed: {total - failed}")
        print(f"   Failed: {failed}")
        print(f"   Content types: {type_counts}")
        print(f"   Output: {output_path}")

        return {'total': total, 'parsed': total - failed, 'failed': failed}


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
        description="ContentParser - 接入内容解析预处理工具"
    )
    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径（jsonl/json/txt）')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--parse_mode', type=str, default='auto',
                        choices=['auto', 'plain', 'markdown', 'html'],
                        help='解析模式，默认auto自动检测')
    parser.add_argument('--extract_title', type=str_to_bool, default=True,
                        help='是否提取标题，默认true')
    parser.add_argument('--extract_paragraphs', type=str_to_bool, default=True,
                        help='是否提取段落列表，默认true')
    parser.add_argument('--output_format', type=str, default='jsonl',
                        choices=['jsonl', 'json', 'auto'],
                        help='输出格式，默认jsonl')

    args = parser.parse_args()

    cp = ContentParser(
        parse_mode=args.parse_mode,
        extract_title=args.extract_title,
        extract_paragraphs=args.extract_paragraphs,
        output_format=args.output_format
    )
    cp.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
