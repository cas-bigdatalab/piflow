import os
import pandas as pd
import warnings
import chardet

# 忽略pandas的一些无关警告，让输出更整洁
warnings.filterwarnings('ignore')


def read_structured_data(file_path: str) -> pd.DataFrame:
    """
    读取结构化数据文件并返回pandas DataFrame
    优化：增加编码自动检测和多编码重试，解决中文编码问题
    :param file_path: 数据文件的完整路径
    :return: 解析后的DataFrame对象
    :raises: FileNotFoundError, ValueError, Exception
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 获取文件扩展名（小写）
    file_ext = os.path.splitext(file_path)[1].lower()

    # 定义常见编码列表（优先尝试）
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    # 根据文件类型调用对应的读取方法
    try:
        if file_ext == '.csv':
            # 第一步：自动检测文件编码
            with open(file_path, 'rb') as f:
                raw_data = f.read(10240)  # 读取前10KB检测编码
                detected_encoding = chardet.detect(raw_data)['encoding']

            # 第二步：优先使用检测到的编码，失败则重试常见编码
            df = None
            # 把检测到的编码放到最前面
            if detected_encoding:
                test_encodings = [detected_encoding] + common_encodings
            else:
                test_encodings = common_encodings

            # 去重，避免重复尝试
            test_encodings = list(dict.fromkeys(test_encodings))

            for encoding in test_encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"[OK] Using encoding {encoding} successfully read CSV file")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue

            if df is None:
                raise Exception("所有编码尝试均失败，无法读取CSV文件")

        elif file_ext == '.tsv':
            # TSV文件同样增加编码重试
            df = None
            for encoding in common_encodings:
                try:
                    df = pd.read_csv(file_path, sep='\t', encoding=encoding)
                    print(f"[OK] Using encoding {encoding} successfully read TSV file")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            if df is None:
                raise Exception("所有编码尝试均失败，无法读取TSV文件")

        elif file_ext in ['.xls', '.xlsx']:
            # Excel文件本身不涉及文本编码问题，直接读取
            df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')

        elif file_ext == '.sav':
            # SPSS文件无需编码处理
            df = pd.read_spss(file_path)

        else:
            raise ValueError(
                f"不支持的文件格式: {file_ext}。目前支持的格式有: csv, tsv, xls, xlsx, sav"
            )

        print(f"成功读取文件: {file_path}，数据形状: {df.shape}")
        return df

    except Exception as e:
        raise Exception(f"读取文件失败: {str(e)}") from e


def write_structured_data(df: pd.DataFrame, output_path: str, **kwargs) -> None:
    """
    将DataFrame写入指定路径的结构化数据文件
    :param df: 要写入的pandas DataFrame
    :param output_path: 输出文件的完整路径
    :param kwargs: 可选参数，传递给pandas的写入方法（如index=False等）
    :raises: ValueError, Exception
    """
    # 验证输入是否为DataFrame
    if not isinstance(df, pd.DataFrame):
        raise ValueError("输入数据必须是pandas DataFrame类型")

    # 获取输出目录并创建（如果不存在）
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取文件扩展名（小写）
    file_ext = os.path.splitext(output_path)[1].lower()

    # 设置默认写入参数
    write_kwargs = {'index': False}
    # 合并用户传入的参数（用户参数优先级更高）
    write_kwargs.update(kwargs)

    # 根据文件类型调用对应的写入方法
    try:
        if file_ext == '.csv':
            df.to_csv(output_path, **write_kwargs)
        elif file_ext == '.tsv':
            df.to_csv(output_path, sep='\t', **write_kwargs)
        elif file_ext == '.xls':
            # xls格式有行数限制，建议使用xlsx
            df.to_excel(output_path, engine='xlwt', **write_kwargs)
        elif file_ext == '.xlsx':
            df.to_excel(output_path, engine='openpyxl', **write_kwargs)
        elif file_ext == '.sav':
            # 写入sav需要安装pyreadstat库
            df.to_spss(output_path, **write_kwargs)
        else:
            raise ValueError(
                f"不支持的文件格式: {file_ext}。目前支持的格式有: csv, tsv, xls, xlsx, sav"
            )

        print(f"成功写入文件: {output_path}")

    except Exception as e:
        raise Exception(f"写入文件失败: {str(e)}") from e


# 测试示例（可选）
if __name__ == "__main__":
    # 1. 测试读取功能
    # 请替换为你自己的测试文件路径
    test_read_path = "森林每木调查数据QC.csv"  # 可以替换为 .tsv/.xlsx/.sav 等
    try:
        df = read_structured_data(test_read_path)
        print("读取的数据预览:")
        print(df.head())
    except Exception as e:
        print(f"读取测试失败: {e}")

    # 2. 测试写入功能
    test_write_path = "森林每木调查数据QC222222.csv"  # 可以替换为其他格式
    try:
        if 'df' in locals():
            write_structured_data(df, test_write_path)
    except Exception as e:
        print(f"写入测试失败: {e}")