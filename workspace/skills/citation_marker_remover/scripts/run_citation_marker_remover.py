import argparse
import json
import os
import re
import warnings

warnings.filterwarnings('ignore')


class CitationMarkerRemover:
    """
    文献引用标记移除工具类
    移除科研文本中的各类引用标记
    """

    # 参考文献章节关键词
    REFERENCE_SECTION_KEYWORDS = [
        'References', 'REFERENCES', 'Bibliography', 'BIBLIOGRAPHY',
        'Works Cited', 'Literature Cited', 'Citations',
        '参考文献', '引用文献', '文献', '参考资料'
    ]

    def __init__(
        self,
        citation_styles: str = 'all',
        remove_inline_refs: bool = True,
        remove_reference_section: bool = False,
        preserve_context: bool = True,
        text_field: str = 'text'
    ):
        self.citation_styles = self._parse_styles(citation_styles)
        self.remove_inline_refs = remove_inline_refs
        self.remove_reference_section = remove_reference_section
        self.preserve_context = preserve_context
        self.text_field = text_field

        # 统计信息
        self.stats = {
            'total': 0,
            'modified': 0,
            'unchanged': 0,
            'citations_removed': 0,
            'numeric_removed': 0,
            'author_year_removed': 0,
            'superscript_removed': 0
        }

    def _parse_styles(self, styles: str) -> list:
        """解析引用格式参数"""
        if styles.lower() == 'all':
            return ['numeric', 'author_year', 'superscript']
        return [s.strip().lower() for s in styles.split(',') if s.strip()]

    def _remove_numeric_citations(self, text: str) -> tuple:
        """移除数字型引用"""
        count = 0
        original = text

        # [1], [2,3], [1-5], [1,3-5]
        pattern1 = r'\[\d+(?:[-,]\d+)*\]'
        matches = re.findall(pattern1, text)
        count += len(matches)
        text = re.sub(pattern1, '', text)

        # (1), (2,3) - avoid matching standalone years like (2020)
        pattern2 = r'\((?:\d{1,3})(?:[-,]\d{1,3})*\)'
        matches = re.findall(pattern2, text)
        count += len(matches)
        text = re.sub(pattern2, '', text)

        # {1}, <1>
        pattern3 = r'[\{<]\d+(?:[-,]\d+)*[\}>]'
        matches = re.findall(pattern3, text)
        count += len(matches)
        text = re.sub(pattern3, '', text)

        # [ref1], [cite1]
        pattern4 = r'\[(?:ref|cite|Ref|Cite)\d+\]'
        matches = re.findall(pattern4, text)
        count += len(matches)
        text = re.sub(pattern4, '', text)

        return text, count

    def _remove_author_year_citations(self, text: str) -> tuple:
        """移除作者年份型引用"""
        count = 0

        # (Smith, 2020), (Smith and Jones, 2020), (Smith et al., 2020)
        # 匹配括号内的作者年份格式
        pattern1 = r'\([A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)?(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?(?:;\s*[A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)?(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?)*\)'
        matches = re.findall(pattern1, text)
        count += len(matches)
        text = re.sub(pattern1, '', text)

        # Smith (2020), Smith and Jones (2020)
        pattern2 = r'[A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)?(?:\s+et\s+al\.?)?\s*\(\d{4}[a-z]?\)'
        matches = re.findall(pattern2, text)
        count += len(matches)
        text = re.sub(pattern2, '', text)

        # (Author1, Year1; Author2, Year2) - 多个引用
        pattern3 = r'\([^)]*\d{4}[^)]*;\s*[^)]*\d{4}[^)]*\)'
        # 只匹配看起来像引用的
        for match in re.finditer(pattern3, text):
            content = match.group()
            # 检查是否包含作者名格式
            if re.search(r'[A-Z][a-z]+', content):
                count += 1
                text = text.replace(content, '', 1)

        return text, count

    def _remove_superscript_citations(self, text: str) -> tuple:
        """移除上标型引用"""
        count = 0

        # Unicode上标数字
        superscript_digits = '\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u2070'
        pattern = f'[{superscript_digits}]+'
        matches = re.findall(pattern, text)
        count += len(matches)
        text = re.sub(pattern, '', text)

        # 上标标记 ^[1] 或 ^1
        pattern2 = r'\^\[?\d+\]?'
        matches = re.findall(pattern2, text)
        count += len(matches)
        text = re.sub(pattern2, '', text)

        return text, count

    def _remove_reference_section(self, text: str) -> str:
        """移除参考文献章节"""
        lines = text.split('\n')
        result_lines = []
        in_reference_section = False

        for line in lines:
            # 检查是否是参考文献章节开始
            stripped = line.strip()
            is_ref_header = False

            for keyword in self.REFERENCE_SECTION_KEYWORDS:
                if stripped == keyword or stripped.startswith(keyword + '\n'):
                    is_ref_header = True
                    break
                # 带序号的标题
                if re.match(rf'^\d+\.?\s*{re.escape(keyword)}', stripped, re.IGNORECASE):
                    is_ref_header = True
                    break

            if is_ref_header:
                in_reference_section = True
                continue

            # 如果遇到新的章节标题，结束参考文献章节
            if in_reference_section:
                # 检查是否是新章节（以数字或#开头的标题）
                if re.match(r'^\d+\.?\s+[A-Z\u4e00-\u9fff]', stripped):
                    in_reference_section = False
                elif re.match(r'^#{1,6}\s+', stripped):
                    in_reference_section = False

            if not in_reference_section:
                result_lines.append(line)

        return '\n'.join(result_lines)

    def _clean_extra_spaces(self, text: str) -> str:
        """清理多余的空格和标点"""
        # 移除引用后可能产生的多余空格
        text = re.sub(r'\s{2,}', ' ', text)

        # 移除标点前的空格
        text = re.sub(r'\s+([,.:;!?])', r'\1', text)

        # 移除空括号
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r'\[\s*\]', '', text)

        # 移除连续的标点（如 ,, 或 ..）
        text = re.sub(r'([,;])\1+', r'\1', text)

        # 移除句首的逗号
        text = re.sub(r'^\s*,\s*', '', text, flags=re.MULTILINE)

        return text.strip()

    def remove_citations(self, text: str) -> tuple:
        """
        移除文本中的引用标记
        返回 (处理后的文本, 移除的引用数量, 各类型统计)
        """
        if not text:
            return text, 0, {}

        total_removed = 0
        type_counts = {
            'numeric': 0,
            'author_year': 0,
            'superscript': 0
        }

        # 移除参考文献章节
        if self.remove_reference_section:
            text = self._remove_reference_section(text)

        # 移除行内引用
        if self.remove_inline_refs:
            if 'numeric' in self.citation_styles:
                text, count = self._remove_numeric_citations(text)
                total_removed += count
                type_counts['numeric'] = count

            if 'author_year' in self.citation_styles:
                text, count = self._remove_author_year_citations(text)
                total_removed += count
                type_counts['author_year'] = count

            if 'superscript' in self.citation_styles:
                text, count = self._remove_superscript_citations(text)
                total_removed += count
                type_counts['superscript'] = count

        # 清理多余空格
        if self.preserve_context:
            text = self._clean_extra_spaces(text)

        return text, total_removed, type_counts

    def _read_input(self, input_path: str) -> tuple:
        """读取输入文件"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"文件不存在: {input_path}")

        file_ext = os.path.splitext(input_path)[1].lower()
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        data = []

        if file_ext == '.jsonl':
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding) as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                data.append(json.loads(line))
                    break
                except UnicodeDecodeError:
                    continue
            return data, 'jsonl'

        elif file_ext == '.json':
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            return data, 'json'
                        else:
                            return [data], 'json'
                except UnicodeDecodeError:
                    continue

        elif file_ext == '.csv':
            import csv
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding, newline='') as f:
                        reader = csv.DictReader(f)
                        data = list(reader)
                    return data, 'csv'
                except UnicodeDecodeError:
                    continue

        elif file_ext in ['.txt', '.md']:
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    return [{self.text_field: content}], 'txt'
                except UnicodeDecodeError:
                    continue

        raise ValueError(f"不支持的文件格式: {file_ext}")

    def _write_output(self, data: list, output_path: str, file_format: str):
        """写入输出文件"""
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if file_format == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

        elif file_format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        elif file_format == 'csv':
            import csv
            if data:
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

        elif file_format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(item.get(self.text_field, ''))

    def perform(self, input_path: str, output_path: str) -> dict:
        """
        执行引用标记移除

        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        :return: 处理结果统计
        """
        # 重置统计
        self.stats = {
            'total': 0,
            'modified': 0,
            'unchanged': 0,
            'citations_removed': 0,
            'numeric_removed': 0,
            'author_year_removed': 0,
            'superscript_removed': 0
        }

        # 读取输入
        data, file_format = self._read_input(input_path)
        self.stats['total'] = len(data)

        # 处理
        for item in data:
            text = item.get(self.text_field, '')
            if not text:
                self.stats['unchanged'] += 1
                continue

            cleaned_text, removed_count, type_counts = self.remove_citations(text)

            if removed_count > 0:
                item[self.text_field] = cleaned_text
                self.stats['modified'] += 1
                self.stats['citations_removed'] += removed_count
                self.stats['numeric_removed'] += type_counts.get('numeric', 0)
                self.stats['author_year_removed'] += type_counts.get('author_year', 0)
                self.stats['superscript_removed'] += type_counts.get('superscript', 0)
            else:
                self.stats['unchanged'] += 1

        # 写入输出
        self._write_output(data, output_path, file_format)

        # 打印结果
        self._print_results(input_path, output_path)

        return self.stats

    def _print_results(self, input_path, output_path):
        """打印处理结果"""
        total = self.stats['total']
        modified = self.stats['modified']
        modified_ratio = modified / total * 100 if total > 0 else 0

        print(f"\n[OK] Citation marker removal completed!")
        print(f"   Input file: {input_path}")
        print(f"   Citation styles: {', '.join(self.citation_styles)}")
        print(f"   Total samples: {total}")
        print(f"   Modified samples: {modified} ({modified_ratio:.1f}%)")
        print(f"   Citations removed: {self.stats['citations_removed']}")
        print(f"   Citation types:")
        print(f"     - Numeric [1]: {self.stats['numeric_removed']}")
        print(f"     - Author-year (Smith, 2020): {self.stats['author_year_removed']}")
        print(f"     - Superscript: {self.stats['superscript_removed']}")
        print(f"   Output file: {output_path}")


def str_to_bool(value):
    """将字符串转换为布尔值"""
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', '1', 'yes'):
        return True
    elif value.lower() in ('false', '0', 'no'):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def main():
    parser = argparse.ArgumentParser(
        description="CitationMarkerRemover - 文献引用标记移除工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--citation_styles', type=str, default='all',
                        help='引用格式：all/numeric/author_year/superscript，默认all')
    parser.add_argument('--remove_inline_refs', type=str_to_bool, default=True,
                        help='是否移除行内引用，默认true')
    parser.add_argument('--remove_reference_section', type=str_to_bool, default=False,
                        help='是否移除参考文献章节，默认false')
    parser.add_argument('--preserve_context', type=str_to_bool, default=True,
                        help='是否保留上下文，默认true')
    parser.add_argument('--text_field', type=str, default='text',
                        help='文本字段名，默认text')

    args = parser.parse_args()

    remover = CitationMarkerRemover(
        citation_styles=args.citation_styles,
        remove_inline_refs=args.remove_inline_refs,
        remove_reference_section=args.remove_reference_section,
        preserve_context=args.preserve_context,
        text_field=args.text_field
    )

    remover.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
