import os
import pandas as pd
import warnings
import chardet

warnings.filterwarnings('ignore')


def read_structured_data(file_path: str) -> pd.DataFrame:
    """
    Read structured data file and return pandas DataFrame
    Optimized: add automatic encoding detection and multi-encoding retry to solve Chinese encoding issues
    :param file_path: Full path to data file
    :return: Parsed DataFrame object
    :raises: FileNotFoundError, ValueError, Exception
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()

    common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    try:
        if file_ext == '.csv':
            with open(file_path, 'rb') as f:
                raw_data = f.read(10244)
                detected_encoding = chardet.detect(raw_data)['encoding']

            df = None
            if detected_encoding:
                test_encodings = [detected_encoding] + common_encodings
            else:
                test_encodings = common_encodings

            test_encodings = list(dict.fromkeys(test_encodings))

            for encoding in test_encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"[OK] Using encoding {encoding} successfully read CSV file")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue

            if df is None:
                raise Exception("All encoding attempts failed, cannot read CSV file")

        elif file_ext == '.tsv':
            df = None
            for encoding in common_encodings:
                try:
                    df = pd.read_csv(file_path, sep='\t', encoding=encoding)
                    print(f"[OK] Using encoding {encoding} successfully read TSV file")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            if df is None:
                raise Exception("All encoding attempts failed, cannot read TSV file")

        elif file_ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')

        elif file_ext == '.sav':
            df = pd.read_spss(file_path)

        else:
            raise ValueError(
                f"Unsupported file format: {file_ext}. Currently supported formats: csv, tsv, xls, xlsx, sav"
            )

        print(f"Successfully read file: {file_path}, data shape: {df.shape}")
        return df

    except Exception as e:
        raise Exception(f"Failed to read file: {str(e)}") from e


def write_structured_data(df: pd.DataFrame, output_path: str, **kwargs) -> None:
    """
    Write DataFrame to specified path as structured data file
    :param df: pandas DataFrame to write
    :param output_path: Full path to output file
    :param kwargs: Optional parameters to pass to pandas write methods (e.g., index=False)
    :raises: ValueError, Exception
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input data must be pandas DataFrame type")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_ext = os.path.splitext(output_path)[1].lower()

    write_kwargs = {'index': False}
    write_kwargs.update(kwargs)

    try:
        if file_ext == '.csv':
            df.to_csv(output_path, **write_kwargs)
        elif file_ext == '.tsv':
            df.to_csv(output_path, sep='\t', **write_kwargs)
        elif file_ext == '.xls':
            df.to_excel(output_path, engine='xlwt', **write_kwargs)
        elif file_ext == '.xlsx':
            df.to_excel(output_path, engine='openpyxl', **write_kwargs)
        elif file_ext == '.sav':
            df.to_spss(output_path, **write_kwargs)
        else:
            raise ValueError(
                f"Unsupported file format: {file_ext}. Currently supported formats: csv, tsv, xls, xlsx, sav"
            )

        print(f"Successfully wrote file: {output_path}")

    except Exception as e:
        raise Exception(f"Failed to write file: {str(e)}") from e


if __name__ == "__main__":
    test_read_path = "test.csv"
    try:
        df = read_structured_data(test_read_path)
        print("Data preview:")
        print(df.head())
    except Exception as e:
        print(f"Read test failed: {e}")

    test_write_path = "test_output.csv"
    try:
        if 'df' in locals():
            write_structured_data(df, test_write_path)
    except Exception as e:
        print(f"Write test failed: {e}")
