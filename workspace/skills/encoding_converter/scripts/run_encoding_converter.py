import argparse
import os
import warnings

warnings.filterwarnings('ignore')

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    chardet = None
    CHARDET_AVAILABLE = False


class EncodingConverter:
    """
    多编码文本统一转换工具类
    自动检测文件编码并转换为目标编码
    """

    # 常见编码列表（按优先级排序）
    COMMON_ENCODINGS = [
        'utf-8',
        'gbk',
        'gb2312',
        'gb18030',
        'big5',
        'shift_jis',
        'euc-jp',
        'euc-kr',
        'latin-1',
        'ascii'
    ]

    # BOM标记
    BOM_MARKERS = {
        b'\xef\xbb\xbf': 'utf-8-sig',
        b'\xff\xfe': 'utf-16-le',
        b'\xfe\xff': 'utf-16-be',
        b'\xff\xfe\x00\x00': 'utf-32-le',
        b'\x00\x00\xfe\xff': 'utf-32-be',
    }

    def __init__(
        self,
        target_encoding: str = 'utf-8',
        source_encoding: str = 'auto',
        recursive: bool = False,
        file_extensions: str = '.txt,.md,.csv,.json,.jsonl',
        error_handling: str = 'replace',
        add_bom: bool = False
    ):
        self.target_encoding = target_encoding.lower()
        self.source_encoding = source_encoding.lower() if source_encoding != 'auto' else 'auto'
        self.recursive = recursive
        self.file_extensions = [ext.strip().lower() for ext in file_extensions.split(',')]
        self.error_handling = error_handling
        self.add_bom = add_bom

        # 统计信息
        self.stats = {
            'total': 0,
            'converted': 0,
            'skipped': 0,
            'failed': 0,
            'encoding_dist': {}
        }

    def _detect_bom(self, data: bytes) -> str:
        """检测BOM标记"""
        for bom, encoding in self.BOM_MARKERS.items():
            if data.startswith(bom):
                return encoding
        return None

    def _detect_encoding(self, file_path: str) -> tuple:
        """
        检测文件编码
        返回 (编码名, 置信度)
        """
        with open(file_path, 'rb') as f:
            raw_data = f.read()

        # 检测BOM
        bom_encoding = self._detect_bom(raw_data)
        if bom_encoding:
            return bom_encoding, 1.0

        # 尝试UTF-8（最常见）
        try:
            raw_data.decode('utf-8')
            return 'utf-8', 0.99
        except UnicodeDecodeError:
            pass

        # 使用chardet检测
        if CHARDET_AVAILABLE:
            result = chardet.detect(raw_data[:10240])  # 只检测前10KB
            if result['encoding'] and result['confidence'] > 0.7:
                return result['encoding'].lower(), result['confidence']

        # 回退：尝试常见编码
        for encoding in self.COMMON_ENCODINGS:
            try:
                raw_data.decode(encoding)
                return encoding, 0.5
            except (UnicodeDecodeError, LookupError):
                continue

        return None, 0.0

    def _convert_file(self, input_path: str, output_path: str) -> dict:
        """
        转换单个文件的编码

        :return: 转换结果信息
        """
        result = {
            'input': input_path,
            'output': output_path,
            'success': False,
            'source_encoding': None,
            'confidence': 0,
            'message': ''
        }

        try:
            # 检测源编码
            if self.source_encoding == 'auto':
                detected_encoding, confidence = self._detect_encoding(input_path)
                if not detected_encoding:
                    result['message'] = '无法检测文件编码'
                    return result
                source_enc = detected_encoding
                result['confidence'] = confidence
            else:
                source_enc = self.source_encoding
                result['confidence'] = 1.0

            result['source_encoding'] = source_enc

            # 读取文件
            with open(input_path, 'rb') as f:
                raw_data = f.read()

            # 解码
            try:
                # 处理BOM
                if source_enc == 'utf-8-sig':
                    text = raw_data.decode('utf-8-sig')
                elif source_enc.startswith('utf-16') or source_enc.startswith('utf-32'):
                    text = raw_data.decode(source_enc)
                else:
                    text = raw_data.decode(source_enc, errors=self.error_handling)
            except (UnicodeDecodeError, LookupError) as e:
                result['message'] = f'解码失败: {str(e)}'
                return result

            # 编码为目标格式
            try:
                if self.add_bom and self.target_encoding == 'utf-8':
                    encoded_data = text.encode('utf-8-sig')
                else:
                    encoded_data = text.encode(self.target_encoding, errors=self.error_handling)
            except (UnicodeEncodeError, LookupError) as e:
                result['message'] = f'编码失败: {str(e)}'
                return result

            # 创建输出目录
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 写入文件
            with open(output_path, 'wb') as f:
                f.write(encoded_data)

            result['success'] = True
            result['input_size'] = len(raw_data)
            result['output_size'] = len(encoded_data)
            result['message'] = 'OK'

        except Exception as e:
            result['message'] = f'处理失败: {str(e)}'

        return result

    def _is_text_file(self, file_path: str) -> bool:
        """判断是否为文本文件"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.file_extensions

    def _collect_files(self, input_path: str) -> list:
        """收集要处理的文件列表"""
        files = []

        if os.path.isfile(input_path):
            if self._is_text_file(input_path):
                files.append(input_path)
        elif os.path.isdir(input_path):
            if self.recursive:
                for root, dirs, filenames in os.walk(input_path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        if self._is_text_file(file_path):
                            files.append(file_path)
            else:
                for filename in os.listdir(input_path):
                    file_path = os.path.join(input_path, filename)
                    if os.path.isfile(file_path) and self._is_text_file(file_path):
                        files.append(file_path)

        return files

    def perform(self, input_path: str, output_path: str) -> dict:
        """
        执行编码转换

        :param input_path: 输入文件或目录路径
        :param output_path: 输出文件或目录路径
        :return: 处理结果统计
        """
        # 重置统计
        self.stats = {
            'total': 0,
            'converted': 0,
            'skipped': 0,
            'failed': 0,
            'encoding_dist': {}
        }

        is_single_file = os.path.isfile(input_path)
        files = self._collect_files(input_path)
        self.stats['total'] = len(files)

        if not files:
            print(f"[WARN] 未找到要处理的文件")
            return self.stats

        results = []

        for file_path in files:
            # 计算输出路径
            if is_single_file:
                out_path = output_path
            else:
                rel_path = os.path.relpath(file_path, input_path)
                out_path = os.path.join(output_path, rel_path)

            # 转换文件
            result = self._convert_file(file_path, out_path)
            results.append(result)

            # 更新统计
            if result['success']:
                self.stats['converted'] += 1
                enc = result['source_encoding']
                self.stats['encoding_dist'][enc] = self.stats['encoding_dist'].get(enc, 0) + 1
            else:
                self.stats['failed'] += 1

        # 打印结果
        self._print_results(input_path, output_path, is_single_file, results)

        return self.stats

    def _print_results(self, input_path, output_path, is_single_file, results):
        """打印处理结果"""
        if is_single_file and results:
            result = results[0]
            if result['success']:
                print(f"\n[OK] Encoding conversion completed!")
                print(f"   Input file: {result['input']}")
                print(f"   Detected encoding: {result['source_encoding']} (confidence: {result['confidence']:.2f})")
                print(f"   Target encoding: {self.target_encoding}")
                print(f"   Output file: {result['output']}")
                print(f"   File size: {result.get('input_size', 0)} bytes -> {result.get('output_size', 0)} bytes")
            else:
                print(f"\n[ERROR] Encoding conversion failed!")
                print(f"   Input file: {result['input']}")
                print(f"   Error: {result['message']}")
        else:
            print(f"\n[OK] Batch encoding conversion completed!")
            print(f"   Input directory: {input_path}")
            print(f"   Output directory: {output_path}")
            print(f"   Target encoding: {self.target_encoding}")
            print(f"   Files processed: {self.stats['total']}")
            print(f"   Successfully converted: {self.stats['converted']}")
            print(f"   Failed: {self.stats['failed']}")

            if self.stats['encoding_dist']:
                print(f"   Encoding distribution:")
                for enc, count in sorted(self.stats['encoding_dist'].items(), key=lambda x: -x[1]):
                    print(f"     - {enc}: {count} files")


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
        description="EncodingConverter - 多编码文本统一转换工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件或目录路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件或目录路径')
    parser.add_argument('--target_encoding', type=str, default='utf-8',
                        help='目标编码，默认utf-8')
    parser.add_argument('--source_encoding', type=str, default='auto',
                        help='源编码，默认auto自动检测')
    parser.add_argument('--recursive', type=str_to_bool, default=False,
                        help='是否递归处理子目录，默认false')
    parser.add_argument('--file_extensions', type=str, default='.txt,.md,.csv,.json,.jsonl',
                        help='要处理的文件扩展名，逗号分隔')
    parser.add_argument('--error_handling', type=str, default='replace',
                        choices=['strict', 'replace', 'ignore'],
                        help='编码错误处理方式，默认replace')
    parser.add_argument('--add_bom', type=str_to_bool, default=False,
                        help='是否添加UTF-8 BOM，默认false')

    args = parser.parse_args()

    converter = EncodingConverter(
        target_encoding=args.target_encoding,
        source_encoding=args.source_encoding,
        recursive=args.recursive,
        file_extensions=args.file_extensions,
        error_handling=args.error_handling,
        add_bom=args.add_bom
    )

    converter.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
