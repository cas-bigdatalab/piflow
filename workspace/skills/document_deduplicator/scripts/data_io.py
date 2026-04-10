import json
import os
from typing import List, Dict, Any


COMMON_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'iso-8859-1']


def _detect_encoding(file_path: str) -> str:
    """自动检测文件编码"""
    for encoding in COMMON_ENCODINGS:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'utf-8'


def read_file(file_path: str, text_key: str = 'text', encoding: str = None) -> List[Dict[str, Any]]:
    """
    根据文件扩展名读取文件并转换为文档列表

    :param file_path: 输入文件路径
    :param text_key: 文本字段的键名 (默认: text)
    :param encoding: 文件编码，默认自动检测
    :return: 文档列表，每个文档是一个字典
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.json':
        return _read_json(file_path, text_key, encoding)
    elif ext == '.txt':
        return _read_txt(file_path, encoding)
    else:
        raise ValueError(f"不支持的文件格式: {ext}，支持的格式: json, txt")


def write_file(data: List[Dict[str, Any]], file_path: str, encoding: str = 'utf-8'):
    """
    根据文件扩展名将数据写入文件

    :param data: 文档列表
    :param file_path: 输出文件路径
    :param encoding: 文件编码 (默认: utf-8)
    """
    ext = os.path.splitext(file_path)[1].lower()

    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)

    if ext == '.json':
        _write_json(data, file_path, encoding)
    elif ext == '.txt':
        _write_txt(data, file_path, encoding)
    else:
        raise ValueError(f"不支持的文件格式: {ext}，支持的格式: json, txt")


def _read_json(file_path: str, text_key: str, encoding: str = None) -> List[Dict[str, Any]]:
    """读取JSON文件"""
    if encoding is None:
        encoding = _detect_encoding(file_path)

    for enc in COMMON_ENCODINGS:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                data = json.load(f)
            break
        except (UnicodeDecodeError, UnicodeError, json.JSONDecodeError):
            if enc == COMMON_ENCODINGS[-1]:
                raise ValueError(f"无法读取JSON文件 {file_path}")
            continue

    if isinstance(data, dict):
        if 'data' in data:
            return data['data']
        elif text_key in data:
            return [{text_key: data[text_key]}]
    elif isinstance(data, list):
        return data

    raise ValueError("JSON格式错误，需要包含 'data' 字段的字典或文档列表")


def _read_txt(file_path: str, encoding: str = None) -> List[Dict[str, Any]]:
    """读取TXT文件，每行作为一个文档"""
    if encoding is None:
        encoding = _detect_encoding(file_path)

    for enc in COMMON_ENCODINGS:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, UnicodeError):
            if enc == COMMON_ENCODINGS[-1]:
                raise ValueError(f"无法读取TXT文件 {file_path}")
            continue

    return [{'text': line.strip()} for line in lines if line.strip()]


def _write_json(data: List[Dict[str, Any]], file_path: str, encoding: str = 'utf-8'):
    """写入JSON文件"""
    with open(file_path, 'w', encoding=encoding) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_txt(data: List[Dict[str, Any]], file_path: str, encoding: str = 'utf-8'):
    """写入TXT文件"""
    with open(file_path, 'w', encoding=encoding) as f:
        for item in data:
            if 'text' in item:
                f.write(item['text'] + '\n')
