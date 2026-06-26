import argparse
import os
import json
import re
import pandas as pd
import warnings

try:
    import jieba
    import jieba.analyse
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

warnings.filterwarnings('ignore')


def read_data(file_path: str) -> pd.DataFrame:
    """读取数据文件"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    if file_ext == '.csv':
        for encoding in common_encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise Exception("无法读取CSV文件")

    elif file_ext == '.tsv':
        for encoding in common_encodings:
            try:
                return pd.read_csv(file_path, sep='\t', encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise Exception("无法读取TSV文件")

    elif file_ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict) and 'data' in data:
            return pd.DataFrame(data['data'])
        else:
            return pd.DataFrame([data])

    elif file_ext == '.jsonl':
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return pd.DataFrame(records)

    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")


def write_data(df: pd.DataFrame, output_path: str):
    """写入数据文件"""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_ext = os.path.splitext(output_path)[1].lower()

    if file_ext == '.csv':
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
    elif file_ext == '.tsv':
        df.to_csv(output_path, sep='\t', index=False, encoding='utf-8-sig')
    elif file_ext == '.json':
        df.to_json(output_path, orient='records', force_ascii=False, indent=2)
    elif file_ext == '.jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')
    else:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')


class KeywordExtractor:
    """关键词提取工具类"""

    def __init__(self, text_field: str, label_field: str = 'keywords', topk: int = 5):
        self.text_field = text_field
        self.label_field = label_field
        self.topk = topk

    def extract(self, text: str) -> str:
        """提取关键词"""
        if pd.isna(text) or not text:
            return json.dumps([], ensure_ascii=False)

        text = str(text)

        if JIEBA_AVAILABLE:
            keywords = jieba.analyse.extract_tags(text, topK=self.topk)
            return json.dumps(keywords, ensure_ascii=False)
        else:
            words = re.findall(r'[一-龥a-zA-Z]+', text)
            word_freq = {}
            for word in words:
                if len(word) >= 2:
                    word_freq[word] = word_freq.get(word, 0) + 1
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [w[0] for w in sorted_words[:self.topk]]
            return json.dumps(keywords, ensure_ascii=False)

    def perform(self, input_path: str, output_path: str):
        """执行关键词提取"""
        df = read_data(input_path)
        total_rows = len(df)

        if self.text_field not in df.columns:
            raise ValueError(f"字段 '{self.text_field}' 不存在。可用字段: {list(df.columns)}")

        df[self.label_field] = df[self.text_field].apply(self.extract)

        write_data(df, output_path)

        print(f"\n[OK] Keyword extraction completed!")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")
        print(f"   Text field: {self.text_field}")
        print(f"   Label field: {self.label_field}")
        print(f"   Top K: {self.topk}")
        print(f"   Total rows: {total_rows}")


def main():
    parser = argparse.ArgumentParser(description="KeywordExtractor - 关键词提取工具")
    parser.add_argument('--input', required=True, type=str, help='输入文件路径')
    parser.add_argument('--output', required=True, type=str, help='输出文件路径')
    parser.add_argument('--text_field', required=True, type=str, help='文本字段名')
    parser.add_argument('--label_field', type=str, default='keywords', help='输出关键词字段名，默认"keywords"')
    parser.add_argument('--topk', type=int, default=5, help='提取关键词数量，默认5')

    args = parser.parse_args()

    extractor = KeywordExtractor(
        text_field=args.text_field,
        label_field=args.label_field,
        topk=args.topk
    )
    extractor.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
