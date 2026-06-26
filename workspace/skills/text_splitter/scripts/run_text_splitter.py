import argparse
import json
import os
import re
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

warnings.filterwarnings('ignore')


@dataclass
class Chunk:
    text: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, object] = field(default_factory=dict)


class TextSplitter:
    SENTENCE_ENDINGS = '。！？.!?'
    SECTIONS_ZH = [
        '摘要', '关键词', '关键字',
        '引言', '前言', '绪论', '导论',
        '研究背景', '背景介绍', '问题背景',
        '文献综述', '相关工作', '研究现状',
        '理论基础', '理论框架',
        '研究方法', '方法', '实验方法', '材料与方法', '材料和方法',
        '研究设计', '实验设计',
        '实验', '实验部分',
        '结果', '实验结果', '结果与分析', '结果分析', '结果与讨论',
        '讨论', '分析与讨论', '分析讨论',
        '结论', '结论与展望', '总结', '结论与建议',
        '致谢', '鸣谢',
        '参考文献', '引用文献', '文献',
        '附录', '附件',
    ]
    SECTIONS_EN = [
        'Abstract', 'Keywords', 'Key Words',
        'Introduction',
        'Background', 'Research Background',
        'Literature Review', 'Related Work', 'Related Works', 'Previous Work',
        'Theoretical Framework', 'Theory',
        'Methods', 'Method', 'Methodology', 'Materials and Methods',
        'Experimental Setup', 'Experiment Setup', 'Experimental Design',
        'Experiments', 'Experiment',
        'Results', 'Result', 'Findings',
        'Results and Discussion', 'Result and Discussion',
        'Discussion', 'Analysis', 'Analysis and Discussion',
        'Conclusion', 'Conclusions', 'Summary', 'Concluding Remarks',
        'Future Work', 'Future Directions',
        'Acknowledgments', 'Acknowledgements', 'Acknowledgment',
        'References', 'Bibliography',
        'Appendix', 'Appendices', 'Supplementary Material',
    ]
    SECTION_NUM_PATTERNS = [
        r'^(\d+)\s*[\.、]?\s*',
        r'^(\d+\.\d+)\s*[\.、]?\s*',
        r'^第[一二三四五六七八九十]+[章节]\s*',
        r'^[一二三四五六七八九十]+[、\.]\s*',
        r'^[IVX]+\s*[\.、]?\s*',
        r'^\([一二三四五六七八九十\d]+\)\s*',
    ]

    def __init__(
        self,
        split_mode: str = 'paragraph',
        max_length: int = 1000,
        overlap: int = 0,
        min_length: int = 10,
        separator: str = 'auto',
        output_format: str = 'jsonl',
        keep_metadata: bool = True,
        text_field: str = 'text',
        language: str = 'auto',
        custom_sections: str = '',
        include_default: bool = True,
        keep_title: bool = True,
        min_section_length: int = 50,
    ):
        self.split_mode = split_mode
        self.max_length = max_length
        self.overlap = overlap
        self.min_length = min_length
        self.separator = separator
        self.output_format = output_format
        self.keep_metadata = keep_metadata
        self.text_field = text_field
        self.language = language
        self.custom_sections = [s.strip() for s in custom_sections.split(',') if s.strip()]
        self.include_default = include_default
        self.keep_title = keep_title
        self.min_section_length = min_section_length

    def _read_input(self, input_path: str) -> str:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f'文件不存在: {input_path}')

        file_ext = os.path.splitext(input_path)[1].lower()
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']

        if file_ext in ['.txt', '.md']:
            return self._read_text_file(input_path, encodings)

        if file_ext == '.json':
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding) as f:
                        data = json.load(f)
                    return self._extract_text_from_json(data)
                except UnicodeDecodeError:
                    continue
            raise Exception('无法解码JSON文件')

        if file_ext == '.jsonl':
            texts = []
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding) as f:
                        for line_no, line in enumerate(f, 1):
                            line = line.strip()
                            if not line:
                                continue
                            obj = json.loads(line)
                            if isinstance(obj, dict):
                                if self.text_field not in obj:
                                    raise ValueError(f"JSONL第{line_no}行未找到'{self.text_field}'字段")
                                texts.append(str(obj[self.text_field]))
                            elif isinstance(obj, str):
                                texts.append(obj)
                            else:
                                raise ValueError(f'JSONL第{line_no}行格式不支持')
                    return '\n\n'.join(texts)
                except UnicodeDecodeError:
                    continue
            raise Exception('无法解码JSONL文件')

        return self._read_text_file(input_path, encodings)

    def _read_text_file(self, input_path: str, encodings: List[str]) -> str:
        for encoding in encodings:
            try:
                with open(input_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise Exception(f'不支持的文件格式或无法解码: {os.path.splitext(input_path)[1].lower()}')

    def _extract_text_from_json(self, data) -> str:
        if isinstance(data, dict):
            if self.text_field in data:
                return str(data[self.text_field])
            if 'text' in data:
                return str(data['text'])
            raise ValueError(f"JSON文件中未找到'{self.text_field}'字段")
        if isinstance(data, str):
            return data
        if isinstance(data, list):
            texts = []
            for index, item in enumerate(data, 1):
                if isinstance(item, dict):
                    if self.text_field not in item:
                        raise ValueError(f"JSON数组第{index}项未找到'{self.text_field}'字段")
                    texts.append(str(item[self.text_field]))
                elif isinstance(item, str):
                    texts.append(item)
                else:
                    raise ValueError(f'JSON数组第{index}项格式不支持')
            return '\n\n'.join(texts)
        raise ValueError('JSON文件格式不支持')

    def _trim_span(self, text: str, start: int, end: int) -> Tuple[int, int]:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        return start, end

    def _resolve_language(self, text: str) -> str:
        if self.language != 'auto':
            return self.language
        chinese_chars = len(re.findall(r'[一-鿿]', text))
        word_chars = len(re.findall(r'\w', text))
        if word_chars == 0:
            return 'zh'
        ratio = chinese_chars / word_chars
        if ratio > 0.3:
            return 'zh'
        if ratio < 0.1:
            return 'en'
        return 'mixed'

    def _build_section_keywords(self, language: str) -> List[str]:
        keywords: List[str] = []
        if self.include_default:
            if language in ['auto', 'zh', 'mixed']:
                keywords.extend(self.SECTIONS_ZH)
            if language in ['auto', 'en', 'mixed']:
                keywords.extend(self.SECTIONS_EN)
        keywords.extend(self.custom_sections)
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            key = keyword.lower()
            if key not in seen:
                seen.add(key)
                unique_keywords.append(keyword)
        unique_keywords.sort(key=len, reverse=True)
        return unique_keywords

    def _normalize_heading(self, line: str) -> str:
        normalized = line.strip()
        for pattern in self.SECTION_NUM_PATTERNS:
            normalized = re.sub(pattern, '', normalized)
        return normalized.strip()

    def _is_section_title(self, line: str, keywords: List[str]) -> Tuple[bool, Optional[str], Optional[str]]:
        stripped = line.strip()
        if not stripped:
            return False, None, None

        normalized = self._normalize_heading(stripped)
        lowered = normalized.lower()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if lowered == keyword_lower:
                return True, keyword, stripped
            if lowered.startswith(keyword_lower):
                rest = normalized[len(keyword):]
                if not rest or rest[0] in ' \t:：。.':
                    return True, keyword, stripped

        for pattern in self.SECTION_NUM_PATTERNS:
            if re.match(pattern, stripped):
                rest = re.sub(pattern, '', stripped).strip()
                for keyword in keywords:
                    if rest.lower().startswith(keyword.lower()):
                        return True, keyword, stripped
                if 0 < len(rest) <= 60 and not re.search(r'[。！？.!?]$', rest):
                    return True, rest, stripped

        return False, None, None

    def _split_by_paragraph(self, text: str) -> List[Chunk]:
        chunks: List[Chunk] = []
        separator = re.compile(r'\r?\n\s*\r?\n')
        start = 0
        for match in separator.finditer(text):
            chunk_start, chunk_end = self._trim_span(text, start, match.start())
            if chunk_start < chunk_end:
                chunks.append(Chunk(text[chunk_start:chunk_end], chunk_start, chunk_end))
            start = match.end()
        chunk_start, chunk_end = self._trim_span(text, start, len(text))
        if chunk_start < chunk_end:
            chunks.append(Chunk(text[chunk_start:chunk_end], chunk_start, chunk_end))
        return chunks

    def _split_by_sentence(self, text: str) -> List[Chunk]:
        chunks: List[Chunk] = []
        pattern = re.compile(r'.*?[。！？.!?]+(?:["\'”’」』]?)', re.S)
        start = 0
        for match in pattern.finditer(text):
            chunk_start, chunk_end = self._trim_span(text, start, match.end())
            if chunk_start < chunk_end:
                chunks.append(Chunk(text[chunk_start:chunk_end], chunk_start, chunk_end))
            start = match.end()
        chunk_start, chunk_end = self._trim_span(text, start, len(text))
        if chunk_start < chunk_end:
            chunks.append(Chunk(text[chunk_start:chunk_end], chunk_start, chunk_end))
        return chunks

    def _find_boundary(self, text: str, start: int, end: int) -> int:
        search_start = start + int((end - start) * 0.8)
        for index in range(end - 1, max(start, search_start) - 1, -1):
            if text[index] in self.SENTENCE_ENDINGS:
                return index + 1
        for index in range(end - 1, max(start, search_start) - 1, -1):
            if text[index] in [' ', '\n', '\t', '，', ',', '；', ';']:
                return index + 1
        return end

    def _split_by_length(self, text: str) -> List[Chunk]:
        if self.max_length <= 0:
            raise ValueError('max_length must be greater than 0')
        if self.overlap < 0:
            raise ValueError('overlap must be non-negative')
        if self.overlap >= self.max_length:
            raise ValueError('overlap must be smaller than max_length to ensure forward progress')

        chunks: List[Chunk] = []
        start = 0
        text_len = len(text)
        while start < text_len:
            raw_end = min(start + self.max_length, text_len)
            boundary_end = raw_end
            if raw_end < text_len:
                boundary_end = self._find_boundary(text, start, raw_end)
                if boundary_end <= start:
                    boundary_end = raw_end
            chunk_start, chunk_end = self._trim_span(text, start, boundary_end)
            if chunk_start < chunk_end:
                chunks.append(Chunk(text[chunk_start:chunk_end], chunk_start, chunk_end))
            if boundary_end >= text_len:
                break
            next_start = boundary_end - self.overlap if self.overlap > 0 else boundary_end
            if next_start <= start:
                next_start = boundary_end
            if next_start <= start:
                next_start = start + 1
            start = next_start
        return chunks

    def _split_by_line(self, text: str) -> List[Chunk]:
        chunks: List[Chunk] = []
        position = 0
        for raw_line in text.splitlines(keepends=True):
            line_start = position
            line_end = position + len(raw_line)
            position = line_end
            line_content_end = line_end
            while line_content_end > line_start and text[line_content_end - 1] in '\r\n':
                line_content_end -= 1
            chunk_start, chunk_end = self._trim_span(text, line_start, line_content_end)
            if chunk_start < chunk_end:
                chunks.append(Chunk(text[chunk_start:chunk_end], chunk_start, chunk_end))
        if text and not text.endswith(('\n', '\r')) and not chunks:
            chunk_start, chunk_end = self._trim_span(text, 0, len(text))
            if chunk_start < chunk_end:
                chunks.append(Chunk(text[chunk_start:chunk_end], chunk_start, chunk_end))
        return chunks

    def _split_by_section(self, text: str) -> List[Chunk]:
        language = self._resolve_language(text)
        keywords = self._build_section_keywords(language)
        lines = text.splitlines(keepends=True)
        if not lines:
            return []

        line_spans: List[Tuple[int, int, int, str]] = []
        position = 0
        for line_number, raw_line in enumerate(lines, 1):
            line_start = position
            line_end = position + len(raw_line)
            position = line_end
            line_content_end = line_end
            while line_content_end > line_start and text[line_content_end - 1] in '\r\n':
                line_content_end -= 1
            line_text = text[line_start:line_content_end]
            line_spans.append((line_number, line_start, line_content_end, line_end, line_text))

        sections: List[Dict[str, object]] = []
        current: Optional[Dict[str, object]] = None

        def finalize(section: Optional[Dict[str, object]]) -> None:
            if not section:
                return
            start_pos = int(section['start_pos'])
            end_pos = int(section['end_pos'])
            if end_pos <= start_pos:
                return
            chunk_text = text[start_pos:end_pos]
            metadata = {
                'section_name': section['section_name'],
                'section_type': section['section_type'],
                'heading_text': section['heading_text'],
                'heading_line': section['heading_line'],
                'start_line': section['start_line'],
                'end_line': section['end_line'],
                'language': language,
            }
            sections.append({
                'text': chunk_text,
                'start_pos': start_pos,
                'end_pos': end_pos,
                'metadata': metadata,
            })

        for line_number, line_start, line_content_end, line_end, line_text in line_spans:
            is_title, section_name, heading_text = self._is_section_title(line_text, keywords)
            if is_title:
                if current is not None:
                    current['end_pos'] = line_start
                    current['end_line'] = line_number - 1
                    finalize(current)
                start_pos = line_start if self.keep_title else line_end
                current = {
                    'section_name': section_name or '正文',
                    'section_type': section_name or 'body',
                    'heading_text': heading_text or '',
                    'heading_line': line_number,
                    'start_line': line_number,
                    'end_line': line_number,
                    'start_pos': start_pos,
                    'end_pos': line_end,
                }
            else:
                if current is None:
                    current = {
                        'section_name': '正文',
                        'section_type': 'body',
                        'heading_text': '',
                        'heading_line': 0,
                        'start_line': line_number,
                        'end_line': line_number,
                        'start_pos': line_start,
                        'end_pos': line_end,
                    }
                current['end_pos'] = line_end
                current['end_line'] = line_number

        finalize(current)

        if self.min_section_length > 0:
            sections = self._merge_short_sections(sections)

        return [Chunk(
            text=section['text'],
            start_pos=section['start_pos'],
            end_pos=section['end_pos'],
            metadata=section['metadata'],
        ) for section in sections]

    def _merge_short_sections(self, sections: List[Dict[str, object]]) -> List[Dict[str, object]]:
        if not sections:
            return sections

        merged: List[Dict[str, object]] = []
        for section in sections:
            if merged and len(str(section['text'])) < self.min_section_length:
                previous = merged[-1]
                previous['text'] = str(previous['text']) + str(section['text'])
                previous['end_pos'] = section['end_pos']
                previous['metadata']['end_line'] = section['metadata']['end_line']
                continue
            merged.append(section)

        if len(merged) > 1 and len(str(merged[0]['text'])) < self.min_section_length:
            merged[1]['text'] = str(merged[0]['text']) + str(merged[1]['text'])
            merged[1]['start_pos'] = merged[0]['start_pos']
            merged[1]['metadata']['start_line'] = merged[0]['metadata']['start_line']
            merged = merged[1:]

        return merged

    def split(self, text: str) -> List[Chunk]:
        if self.split_mode == 'paragraph':
            chunks = self._split_by_paragraph(text)
        elif self.split_mode == 'sentence':
            chunks = self._split_by_sentence(text)
        elif self.split_mode == 'length':
            chunks = self._split_by_length(text)
        elif self.split_mode == 'line':
            chunks = self._split_by_line(text)
        elif self.split_mode == 'section':
            chunks = self._split_by_section(text)
        else:
            raise ValueError(f'不支持的切分模式: {self.split_mode}')

        if self.split_mode != 'section' and self.min_length > 0:
            chunks = self._merge_short_chunks(chunks)

        return chunks

    def _merge_short_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        if not chunks:
            return chunks

        merged: List[Chunk] = []
        for chunk in chunks:
            if merged and len(chunk.text) < self.min_length:
                previous = merged[-1]
                previous.text = previous.text + chunk.text
                previous.end_pos = chunk.end_pos
                continue
            merged.append(chunk)

        if len(merged) > 1 and len(merged[0].text) < self.min_length:
            merged[1].text = merged[0].text + merged[1].text
            merged[1].start_pos = merged[0].start_pos
            merged = merged[1:]

        return merged

    def _chunk_to_record(self, chunk_id: int, chunk: Chunk, source_file: str) -> Dict[str, object]:
        record: Dict[str, object] = {
            'chunk_id': chunk_id,
            'text': chunk.text,
        }
        if self.keep_metadata:
            record['start_pos'] = chunk.start_pos
            record['end_pos'] = chunk.end_pos
            record['source'] = os.path.basename(source_file)
            record.update(chunk.metadata)
        return record

    def _write_output(self, chunks: List[Chunk], output_path: str, source_file: str) -> None:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if self.output_format == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for chunk_id, chunk in enumerate(chunks):
                    record = self._chunk_to_record(chunk_id, chunk, source_file)
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            return

        if self.output_format == 'json':
            records = [self._chunk_to_record(chunk_id, chunk, source_file) for chunk_id, chunk in enumerate(chunks)]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            return

        if self.output_format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                if self.split_mode == 'section':
                    for chunk in chunks:
                        section_name = chunk.metadata.get('section_name', '正文')
                        f.write(f'=== {section_name} ===\n')
                        f.write(chunk.text)
                        f.write('\n\n')
                else:
                    separator = '\n\n---\n\n' if self.separator == 'auto' else self.separator
                    f.write(separator.join(chunk.text for chunk in chunks))
            return

        raise ValueError(f'不支持的输出格式: {self.output_format}')

    def perform(self, input_path: str, output_path: str) -> Dict[str, object]:
        text = self._read_input(input_path)
        chunks = self.split(text)
        self._write_output(chunks, output_path, input_path)

        avg_length = sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0
        result = {
            'input_file': input_path,
            'output_file': output_path,
            'split_mode': self.split_mode,
            'split_count': len(chunks),
            'avg_chunk_length': int(avg_length),
        }
        if self.split_mode == 'section':
            result['language'] = self._resolve_language(text)
        print('\n[OK] Text split completed!')
        print(f'   Input file: {input_path}')
        print(f'   Split mode: {self.split_mode}')
        if self.split_mode == 'section':
            print(f'   Language: {result["language"]}')
        print(f'   Split count: {len(chunks)}')
        print(f'   Output file: {output_path}')
        print(f'   Average chunk length: {int(avg_length)} chars')
        return result


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', '1', 'yes'):
        return True
    if value.lower() in ('false', '0', 'no'):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='TextSplitter - 长文本规则切分工具')
    parser.add_argument('--input', required=True, type=str, help='输入文件路径')
    parser.add_argument('--output', required=True, type=str, help='输出文件路径')
    parser.add_argument('--split_mode', type=str, default='paragraph', choices=['paragraph', 'sentence', 'length', 'line', 'section'], help='切分模式，默认paragraph')
    parser.add_argument('--max_length', type=int, default=1000, help='length模式下的最大字符数，默认1000')
    parser.add_argument('--overlap', type=int, default=0, help='length模式下的重叠字符数，默认0')
    parser.add_argument('--min_length', type=int, default=10, help='最小片段长度，默认10')
    parser.add_argument('--separator', type=str, default='auto', help='自定义分隔符，默认auto')
    parser.add_argument('--output_format', type=str, default='jsonl', choices=['jsonl', 'json', 'txt'], help='输出格式，默认jsonl')
    parser.add_argument('--keep_metadata', type=str_to_bool, default=True, help='是否保留元信息，默认true')
    parser.add_argument('--text_field', type=str, default='text', help='JSON/JSONL输入时的文本字段名，默认text')
    parser.add_argument('--language', type=str, default='auto', choices=['auto', 'zh', 'en', 'mixed'], help='论文语言，默认auto')
    parser.add_argument('--custom_sections', type=str, default='', help='自定义章节关键词，逗号分隔')
    parser.add_argument('--include_default', type=str_to_bool, default=True, help='是否包含默认章节关键词，默认true')
    parser.add_argument('--keep_title', type=str_to_bool, default=True, help='是否在章节内容中保留章节标题，默认true')
    parser.add_argument('--min_section_length', type=int, default=50, help='最小章节长度，低于此长度的章节将被合并，默认50')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    splitter = TextSplitter(
        split_mode=args.split_mode,
        max_length=args.max_length,
        overlap=args.overlap,
        min_length=args.min_length,
        separator=args.separator,
        output_format=args.output_format,
        keep_metadata=args.keep_metadata,
        text_field=args.text_field,
        language=args.language,
        custom_sections=args.custom_sections,
        include_default=args.include_default,
        keep_title=args.keep_title,
        min_section_length=args.min_section_length,
    )
    splitter.perform(input_path=args.input, output_path=args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
