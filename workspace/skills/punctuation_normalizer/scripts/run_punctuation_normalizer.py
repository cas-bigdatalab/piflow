import argparse
import json
import os
import re
import warnings

warnings.filterwarnings('ignore')


class PunctuationNormalizer:
    """
    文本标点规范化工具类
    规范化文本中的标点符号
    """

    # 全角标点
    FULL_WIDTH_PUNCTS = "，。！？；：“”‘’（）【】《》、"
    # 半角标点
    HALF_WIDTH_PUNCTS = ',.!?;:"\'\(\)\[\]<>/'

    # 全角到半角映射
    FULL_TO_HALF = {
        '，': ',', '。': '.', '！': '!', '？': '?',
        '；': ';', '：': ':', '“': '"', '”': '"',
        '‘': "'", '’': "'", '（': '(', '）': ')',
        '【': '[', '】': ']', '《': '<', '》': '>',
        '、': ',', '～': '~', '　': ' '
    }

    # 半角到全角映射
    HALF_TO_FULL = {v: k for k, v in FULL_TO_HALF.items()}
    # 特殊处理引号
    HALF_TO_FULL['"'] = '"'
    HALF_TO_FULL["'"] = '‘'

    # 可重复的标点
    REPEATABLE_PUNCTS = '！？!?、,，;；:：'

    def __init__(
        self,
        merge_repeated: bool = True,
        max_repeat: int = 1,
        normalize_width: str = 'auto',
        normalize_quotes: bool = True,
        quote_style: str = 'chinese',
        normalize_ellipsis: bool = True,
        remove_space_around_punct: bool = True,
        text_field: str = 'text'
    ):
        self.merge_repeated = merge_repeated
        self.max_repeat = max_repeat
        self.normalize_width = normalize_width
        self.normalize_quotes = normalize_quotes
        self.quote_style = quote_style
        self.normalize_ellipsis = normalize_ellipsis
        self.remove_space_around_punct = remove_space_around_punct
        self.text_field = text_field

        # 统计信息
        self.stats = {
            'total': 0,
            'modified': 0,
            'unchanged': 0,
            'merged_repeated': 0,
            'normalized_width': 0,
            'normalized_quotes': 0,
            'normalized_ellipsis': 0,
            'removed_spaces': 0
        }

    def _detect_language(self, text: str) -> str:
        """检测文本主要语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        if chinese_chars > english_chars:
            return 'chinese'
        else:
            return 'english'

    def _merge_repeated_puncts(self, text: str) -> tuple:
        """合并重复标点"""
        modified = False
        original = text

        for punct in self.REPEATABLE_PUNCTS:
            # 匹配连续重复的标点
            pattern = f'[{re.escape(punct)}]{{2,}}'
            if re.search(pattern, text):
                replacement = punct * self.max_repeat
                text = re.sub(pattern, replacement, text)
                modified = True

        # 处理混合重复（如 ！？！？）
        mixed_pattern = r'[！？!?]{2,}'
        if re.search(mixed_pattern, text):
            # 保留第一个标点
            def replace_mixed(match):
                return match.group(0)[0] * self.max_repeat
            text = re.sub(mixed_pattern, replace_mixed, text)
            modified = True

        return text, modified

    def _normalize_width(self, text: str, target: str) -> tuple:
        """全半角规范化"""
        modified = False
        original = text

        if target == 'full':
            # 转全角
            for half, full in self.HALF_TO_FULL.items():
                if half in text:
                    text = text.replace(half, full)
                    modified = True
        elif target == 'half':
            # 转半角
            for full, half in self.FULL_TO_HALF.items():
                if full in text:
                    text = text.replace(full, half)
                    modified = True

        return text, modified

    def _normalize_quotes(self, text: str, style: str) -> tuple:
        """规范化引号"""
        modified = False

        if style == 'chinese':
            patterns = [
                (r'""([^\"]+)""', r'“\1”'),
                (r'"([^\"]+)"', r'“\1”'),
                (r"''([^']+)''", r'‘\1’'),
                (r"'([^']+)'", r'‘\1’'),
                (r'«([^»]+)»', r'“\1”'),
                (r'“([^”]+)”', r'“\1”'),
                (r'‘([^’]+)’', r'‘\1’'),
            ]
            for pattern, replacement in patterns:
                new_text, count = re.subn(pattern, replacement, text)
                if count:
                    text = new_text
                    modified = True

        elif style == 'english':
            patterns = [
                (r'""([^\"]+)""', r'"\1"'),
                (r'“([^”]+)”', r'"\1"'),
                (r'"([^\"]+)"', r'"\1"'),
                (r"''([^']+)''", r"'\1'"),
                (r'‘([^’]+)’', r"'\1'"),
                (r"'([^']+)'", r"'\1'"),
                (r'「([^」]+)」', r'"\1"'),
                (r'『([^』]+)』', r"'\1'"),
            ]
            for pattern, replacement in patterns:
                new_text, count = re.subn(pattern, replacement, text)
                if count:
                    text = new_text
                    modified = True

        return text, modified

    def _normalize_ellipsis(self, text: str) -> tuple:
        """规范化省略号"""
        modified = False
        original = text

        # 各种省略号形式
        patterns = [
            (r'\.{3,}', '……'),      # ...
            (r'。{2,}', '……'),       # 。。。
            (r'·{3,}', '……'),       # ···
            (r'…+', '……'),          # 多个省略号
            (r'\.{2}', '……'),       # ..
        ]

        for pattern, replacement in patterns:
            if re.search(pattern, text):
                text = re.sub(pattern, replacement, text)
                modified = True

        return text, modified

    def _remove_space_around_punct(self, text: str) -> tuple:
        """移除标点周围的多余空格"""
        modified = False
        original = text

        # 中文标点前后的空格
        chinese_puncts = '，。！？；：、（）【】《》'
        for punct in chinese_puncts:
            # 标点前的空格
            pattern = r'\s+' + re.escape(punct)
            if re.search(pattern, text):
                text = re.sub(pattern, punct, text)
                modified = True
            # 标点后的空格（保留换行）
            pattern = re.escape(punct) + r'[ \t]+'
            if re.search(pattern, text):
                text = re.sub(pattern, punct, text)
                modified = True

        # 多个连续空格合并为一个
        if re.search(r'[ \t]{2,}', text):
            text = re.sub(r'[ \t]{2,}', ' ', text)
            modified = True

        return text, modified

    def normalize(self, text: str) -> tuple:
        """
        规范化文本标点
        返回 (规范化后的文本, 是否被修改)
        """
        if not text:
            return text, False

        modified = False
        modifications = []

        # 1. 合并重复标点
        if self.merge_repeated:
            text, m = self._merge_repeated_puncts(text)
            if m:
                modified = True
                modifications.append('merged_repeated')

        # 2. 全半角规范化
        if self.normalize_width != 'none':
            if self.normalize_width == 'auto':
                lang = self._detect_language(text)
                target = 'half' if lang == 'chinese' else 'half'
            else:
                target = self.normalize_width

            text, m = self._normalize_width(text, target)
            if m:
                modified = True
                modifications.append('normalized_width')

        # 3. 引号规范化
        if self.normalize_quotes:
            text, m = self._normalize_quotes(text, self.quote_style)
            if m:
                modified = True
                modifications.append('normalized_quotes')

        # 4. 省略号规范化
        if self.normalize_ellipsis:
            text, m = self._normalize_ellipsis(text)
            if m:
                modified = True
                modifications.append('normalized_ellipsis')

        # 5. 移除标点周围空格
        if self.remove_space_around_punct:
            text, m = self._remove_space_around_punct(text)
            if m:
                modified = True
                modifications.append('removed_spaces')

        return text, modified, modifications

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
        执行标点规范化

        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        :return: 处理结果统计
        """
        # 重置统计
        self.stats = {
            'total': 0,
            'modified': 0,
            'unchanged': 0,
            'merged_repeated': 0,
            'normalized_width': 0,
            'normalized_quotes': 0,
            'normalized_ellipsis': 0,
            'removed_spaces': 0
        }

        # 读取输入
        data, file_format = self._read_input(input_path)
        self.stats['total'] = len(data)

        # 规范化
        for item in data:
            text = item.get(self.text_field, '')
            if not text:
                self.stats['unchanged'] += 1
                continue

            normalized_text, modified, modifications = self.normalize(text)

            if modified:
                item[self.text_field] = normalized_text
                self.stats['modified'] += 1
                for mod in modifications:
                    self.stats[mod] = self.stats.get(mod, 0) + 1
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
        unchanged = self.stats['unchanged']
        modified_ratio = modified / total * 100 if total > 0 else 0
        unchanged_ratio = unchanged / total * 100 if total > 0 else 0

        print(f"\n[OK] Punctuation normalization completed!")
        print(f"   Input file: {input_path}")
        print(f"   Total samples: {total}")
        print(f"   Modified samples: {modified} ({modified_ratio:.1f}%)")
        print(f"   Unchanged samples: {unchanged} ({unchanged_ratio:.1f}%)")
        print(f"   Modifications:")
        print(f"     - Merged repeated punctuation: {self.stats.get('merged_repeated', 0)}")
        print(f"     - Normalized width: {self.stats.get('normalized_width', 0)}")
        print(f"     - Normalized quotes: {self.stats.get('normalized_quotes', 0)}")
        print(f"     - Normalized ellipsis: {self.stats.get('normalized_ellipsis', 0)}")
        print(f"     - Removed extra spaces: {self.stats.get('removed_spaces', 0)}")
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
        description="PunctuationNormalizer - 文本标点规范化工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--merge_repeated', type=str_to_bool, default=True,
                        help='是否合并重复标点，默认true')
    parser.add_argument('--max_repeat', type=int, default=1,
                        help='允许的最大重复次数，默认1')
    parser.add_argument('--normalize_width', type=str, default='auto',
                        choices=['auto', 'full', 'half', 'none'],
                        help='全半角规范化，默认auto')
    parser.add_argument('--normalize_quotes', type=str_to_bool, default=True,
                        help='是否规范化引号，默认true')
    parser.add_argument('--quote_style', type=str, default='chinese',
                        choices=['chinese', 'english'],
                        help='引号风格，默认chinese')
    parser.add_argument('--normalize_ellipsis', type=str_to_bool, default=True,
                        help='是否规范化省略号，默认true')
    parser.add_argument('--remove_space_around_punct', type=str_to_bool, default=True,
                        help='是否移除标点周围空格，默认true')
    parser.add_argument('--text_field', type=str, default='text',
                        help='文本字段名，默认text')

    args = parser.parse_args()

    normalizer = PunctuationNormalizer(
        merge_repeated=args.merge_repeated,
        max_repeat=args.max_repeat,
        normalize_width=args.normalize_width,
        normalize_quotes=args.normalize_quotes,
        quote_style=args.quote_style,
        normalize_ellipsis=args.normalize_ellipsis,
        remove_space_around_punct=args.remove_space_around_punct,
        text_field=args.text_field
    )

    normalizer.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
