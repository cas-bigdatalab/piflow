import os
import pandas as pd
import warnings
try:
    import chardet
except ImportError:
    chardet = None

# 蹇界暐pandas鐨勪竴浜涙棤鍏宠鍛婏紝璁╄緭鍑烘洿鏁存磥
warnings.filterwarnings('ignore')


def read_structured_data(file_path: str) -> pd.DataFrame:
    """
    璇诲彇缁撴瀯鍖栨暟鎹枃浠跺苟杩斿洖pandas DataFrame
    浼樺寲锛氬鍔犵紪鐮佽嚜鍔ㄦ娴嬪拰澶氱紪鐮侀噸璇曪紝瑙ｅ喅涓枃缂栫爜闂
    :param file_path: 鏁版嵁鏂囦欢鐨勫畬鏁磋矾寰?
    :return: 瑙ｆ瀽鍚庣殑DataFrame瀵硅薄
    :raises: FileNotFoundError, ValueError, Exception
    """
    # 妫€鏌ユ枃浠舵槸鍚﹀瓨鍦?
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"鏂囦欢涓嶅瓨鍦? {file_path}")

    # 鑾峰彇鏂囦欢鎵╁睍鍚嶏紙灏忓啓锛?
    file_ext = os.path.splitext(file_path)[1].lower()

    # 瀹氫箟甯歌缂栫爜鍒楄〃锛堜紭鍏堝皾璇曪級
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']

    # 鏍规嵁鏂囦欢绫诲瀷璋冪敤瀵瑰簲鐨勮鍙栨柟娉?
    try:
        if file_ext == '.csv':
            # 绗竴姝ワ細鑷姩妫€娴嬫枃浠剁紪鐮?
            detected_encoding = None
            if chardet is not None:
                with open(file_path, 'rb') as f:
                    raw_data = f.read(10240)
                    detected_encoding = chardet.detect(raw_data)['encoding']

            # 绗簩姝ワ細浼樺厛浣跨敤妫€娴嬪埌鐨勭紪鐮侊紝澶辫触鍒欓噸璇曞父瑙佺紪鐮?
            df = None
            # 鎶婃娴嬪埌鐨勭紪鐮佹斁鍒版渶鍓嶉潰
            if detected_encoding:
                test_encodings = [detected_encoding] + common_encodings
            else:
                test_encodings = common_encodings

            # 鍘婚噸锛岄伩鍏嶉噸澶嶅皾璇?
            test_encodings = list(dict.fromkeys(test_encodings))

            for encoding in test_encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"[OK] Using encoding {encoding} successfully read CSV file")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue

            if df is None:
                raise Exception("鎵€鏈夌紪鐮佸皾璇曞潎澶辫触锛屾棤娉曡鍙朇SV鏂囦欢")

        elif file_ext == '.tsv':
            # TSV鏂囦欢鍚屾牱澧炲姞缂栫爜閲嶈瘯
            df = None
            for encoding in common_encodings:
                try:
                    df = pd.read_csv(file_path, sep='\t', encoding=encoding)
                    print(f"[OK] Using encoding {encoding} successfully read TSV file")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            if df is None:
                raise Exception("鎵€鏈夌紪鐮佸皾璇曞潎澶辫触锛屾棤娉曡鍙朤SV鏂囦欢")

        elif file_ext in ['.xls', '.xlsx']:
            # Excel鏂囦欢鏈韩涓嶆秹鍙婃枃鏈紪鐮侀棶棰橈紝鐩存帴璇诲彇
            df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')

        elif file_ext == '.sav':
            # SPSS鏂囦欢鏃犻渶缂栫爜澶勭悊
            df = pd.read_spss(file_path)

        else:
            raise ValueError(
                f"涓嶆敮鎸佺殑鏂囦欢鏍煎紡: {file_ext}銆傜洰鍓嶆敮鎸佺殑鏍煎紡鏈? csv, tsv, xls, xlsx, sav"
            )

        try:
            print(f"鎴愬姛璇诲彇鏂囦欢: {file_path}锛屾暟鎹舰鐘? {df.shape}")
        except UnicodeEncodeError:
            print(f"Read file OK: {file_path}, shape: {df.shape}")
        return df

    except Exception as e:
        raise Exception(f"璇诲彇鏂囦欢澶辫触: {str(e)}") from e


def write_structured_data(df: pd.DataFrame, output_path: str, **kwargs) -> None:
    """
    灏咲ataFrame鍐欏叆鎸囧畾璺緞鐨勭粨鏋勫寲鏁版嵁鏂囦欢
    :param df: 瑕佸啓鍏ョ殑pandas DataFrame
    :param output_path: 杈撳嚭鏂囦欢鐨勫畬鏁磋矾寰?
    :param kwargs: 鍙€夊弬鏁帮紝浼犻€掔粰pandas鐨勫啓鍏ユ柟娉曪紙濡俰ndex=False绛夛級
    :raises: ValueError, Exception
    """
    # 楠岃瘉杈撳叆鏄惁涓篋ataFrame
    if not isinstance(df, pd.DataFrame):
        raise ValueError("杈撳叆鏁版嵁蹇呴』鏄痯andas DataFrame绫诲瀷")

    # 鑾峰彇杈撳嚭鐩綍骞跺垱寤猴紙濡傛灉涓嶅瓨鍦級
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 鑾峰彇鏂囦欢鎵╁睍鍚嶏紙灏忓啓锛?
    file_ext = os.path.splitext(output_path)[1].lower()

    # 璁剧疆榛樿鍐欏叆鍙傛暟
    write_kwargs = {'index': False}
    # 鍚堝苟鐢ㄦ埛浼犲叆鐨勫弬鏁帮紙鐢ㄦ埛鍙傛暟浼樺厛绾ф洿楂橈級
    write_kwargs.update(kwargs)

    # 鏍规嵁鏂囦欢绫诲瀷璋冪敤瀵瑰簲鐨勫啓鍏ユ柟娉?
    try:
        if file_ext == '.csv':
            df.to_csv(output_path, **write_kwargs)
        elif file_ext == '.tsv':
            df.to_csv(output_path, sep='\t', **write_kwargs)
        elif file_ext == '.xls':
            # xls鏍煎紡鏈夎鏁伴檺鍒讹紝寤鸿浣跨敤xlsx
            df.to_excel(output_path, engine='xlwt', **write_kwargs)
        elif file_ext == '.xlsx':
            df.to_excel(output_path, engine='openpyxl', **write_kwargs)
        elif file_ext == '.sav':
            # 鍐欏叆sav闇€瑕佸畨瑁卲yreadstat搴?
            df.to_spss(output_path, **write_kwargs)
        else:
            raise ValueError(
                f"涓嶆敮鎸佺殑鏂囦欢鏍煎紡: {file_ext}銆傜洰鍓嶆敮鎸佺殑鏍煎紡鏈? csv, tsv, xls, xlsx, sav"
            )

        try:
            print(f"鎴愬姛鍐欏叆鏂囦欢: {output_path}")
        except UnicodeEncodeError:
            print(f"Write file OK: {output_path}")

    except Exception as e:
        raise Exception(f"鍐欏叆鏂囦欢澶辫触: {str(e)}") from e


# 娴嬭瘯绀轰緥锛堝彲閫夛級
if __name__ == "__main__":
    # 1. 娴嬭瘯璇诲彇鍔熻兘
    # 璇锋浛鎹负浣犺嚜宸辩殑娴嬭瘯鏂囦欢璺緞
    test_read_path = "妫灄姣忔湪璋冩煡鏁版嵁QC.csv"  # 鍙互鏇挎崲涓?.tsv/.xlsx/.sav 绛?
    try:
        df = read_structured_data(test_read_path)
        print("璇诲彇鐨勬暟鎹瑙?")
        print(df.head())
    except Exception as e:
        print(f"璇诲彇娴嬭瘯澶辫触: {e}")

    # 2. 娴嬭瘯鍐欏叆鍔熻兘
    test_write_path = "妫灄姣忔湪璋冩煡鏁版嵁QC222222.csv"  # 鍙互鏇挎崲涓哄叾浠栨牸寮?
    try:
        if 'df' in locals():
            write_structured_data(df, test_write_path)
    except Exception as e:
        print(f"鍐欏叆娴嬭瘯澶辫触: {e}")