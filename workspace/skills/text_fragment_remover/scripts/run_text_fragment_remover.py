import argparse
import os
import json
import pandas as pd
import warnings

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
    elif file_ext in ['.xlsx', '.xls']:
        df.to_excel(output_path, index=False)
    elif file_ext == '.json':
        df.to_json(output_path, orient='records', force_ascii=False, indent=2)
    elif file_ext == '.jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')
    else:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')


class TextStripper:
    """指定片段删除工具类"""

    def __init__(self, remove_texts: list):
        self.remove_texts = [item for item in remove_texts if item]

    def strip_fragments(self, text):
        if not isinstance(text, str):
            return text

        result = text
        for fragment in self.remove_texts:
            result = result.replace(fragment, '')
        return result

    def perform(self, input_path: str, output_path: str, text_field: str):
        """执行指定片段删除"""
        df = read_data(input_path)
        total_rows = len(df)

        if text_field not in df.columns:
            raise ValueError(f"字段 '{text_field}' 不存在。可用字段: {list(df.columns)}")

        original_values = df[text_field].copy()
        df[text_field] = df[text_field].apply(self.strip_fragments)
        modified_count = (original_values != df[text_field]).sum()

        write_data(df, output_path)

        print(f"\n[OK] Text fragment stripping completed!")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")
        print(f"   Text field: {text_field}")
        print(f"   Remove texts: {', '.join(self.remove_texts)}")
        print(f"   Total rows: {total_rows}")
        print(f"   Rows modified: {modified_count}")


def parse_remove_texts(raw_value: str) -> list:
    parts = []
    for line in raw_value.splitlines():
        parts.extend([item.strip() for item in line.split('||')])
    return [item for item in parts if item]


def main():
    parser = argparse.ArgumentParser(
        description="TextStripper - 指定文本片段删除工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--text_field', required=True, type=str,
                        help='文本字段名')
    parser.add_argument('--remove_texts', required=True, type=str,
                        help='要删除的文本片段，支持用 || 或换行分隔多个片段')

    args = parser.parse_args()

    remove_texts = parse_remove_texts(args.remove_texts)
    if not remove_texts:
        raise ValueError('remove_texts 不能为空')

    stripper = TextStripper(remove_texts=remove_texts)
    stripper.perform(
        input_path=args.input,
        output_path=args.output,
        text_field=args.text_field
    )


if __name__ == '__main__':
    main()
