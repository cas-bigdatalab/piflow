import argparse
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import data_io  # 导入data_io工具模块


class QC14_TimePeakValue:
    """
    尖峰检验：连续剧烈变化检测
    主要用于时间序列数据，识别在连续N次的相邻读数之间的差值（变化量）的绝对值都高于预设的阈值
    """

    def __init__(self, conditions: str, time_field: str, time_format: str, qc_mark: str, mark_field_name: str):
        self.conditions = conditions
        self.time_field = time_field
        self.time_format = time_format
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name

        # 解析条件配置
        self.fields_config: Dict[str, Tuple[float, int]] = self._parse_conditions()

    def _parse_conditions(self) -> Dict[str, Tuple[float, int]]:
        """
        解析条件字符串，格式示例：
        Do_ppm,1,3
        Temp_C,2,4
        pH,4,5
        Sal,3,4
        返回：{字段名: (峰值阈值, 连续次数)}
        """
        config = {}
        lines = [line.strip() for line in self.conditions.split('\n') if line.strip()]
        for line in lines:
            parts = line.split(',')
            if len(parts) != 3:
                raise ValueError(f"Invalid condition format, line: {line}, expected: field_name,threshold,count")
            field = parts[0].strip()
            lift = float(parts[1].strip())
            n = int(parts[2].strip())
            config[field] = (lift, n)
        return config

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理数据：转换时间格式，备份原始时间字段"""
        df = df.copy()
        # 备份时间字段
        time_field_backup = f"{self.time_field}_origin_backup"
        df[time_field_backup] = df[self.time_field]

        # 转换时间字段为datetime类型
        try:
            df[self.time_field] = pd.to_datetime(df[self.time_field], format=self.time_format)
        except Exception as e:
            raise ValueError(f"Time field format failed, format: {self.time_format}, error: {str(e)}")

        # 按时间排序
        df = df.sort_values(by=self.time_field).reset_index(drop=True)
        return df

    def _add_lagged_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """为每个监测字段添加滞后值列"""
        df = df.copy()
        for field, (_, n) in self.fields_config.items():
            # 生成从lag1到lag(n-1)的滞后列
            for i in range(1, n):
                df[f"{field}_lag{i}"] = df[field].shift(i)
        return df

    def _detect_peak_anomaly(self, df: pd.DataFrame) -> pd.DataFrame:
        """检测尖峰异常，标记异常状态"""
        df = df.copy()
        temp_status_cols = []

        # 为每个字段创建异常状态临时列
        for field, (lift, n) in self.fields_config.items():
            temp_col = f"{field}_status_temp"
            temp_status_cols.append(temp_col)

            # 构建连续n-1个差值都大于等于阈值的条件
            conditions = []
            for i in range(1, n):
                # 获取当前值和前一个滞后值
                if i == 1:
                    current_val = df[field]
                else:
                    current_val = df[f"{field}_lag{i - 1}"]
                prev_val = df[f"{field}_lag{i}"]

                # 计算绝对差值，过滤空值，判断是否大于等于阈值
                abs_diff = abs(current_val - prev_val)
                cond = (abs_diff >= lift) & current_val.notna() & prev_val.notna()
                conditions.append(cond)

            # 组合所有条件（所有差值都满足）
            if conditions:
                anomaly_cond = conditions[0]
                for cond in conditions[1:]:
                    anomaly_cond = anomaly_cond & cond
            else:
                anomaly_cond = pd.Series([False] * len(df))

            # 标记异常字段名，否则为NaN
            df[temp_col] = np.where(anomaly_cond, field, np.nan)

        # 合并所有异常标记
        df['consolidated_anomaly'] = df[temp_status_cols].apply(
            lambda row: ','.join([str(x) for x in row if pd.notna(x)]), axis=1
        )

        # 生成最终的质控标记
        df[self.mark_field_name] = np.where(
            df['consolidated_anomaly'] != '',
            f"{self.qc_mark}({df['consolidated_anomaly']})",
            np.nan
        )

        return df

    def _merge_results(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> pd.DataFrame:
        """合并原始数据和检测结果"""
        # 只保留需要的列用于合并
        merge_cols = [f"{self.time_field}_origin_backup", self.mark_field_name]
        temp_df = processed_df[merge_cols].copy()

        # 重命名备份时间字段，用于和原始数据合并
        temp_df.rename(columns={f"{self.time_field}_origin_backup": self.time_field}, inplace=True)

        # 左连接原始数据
        merged_df = original_df.merge(temp_df, on=self.time_field, how='left', suffixes=('', '_new'))

        # 合并质控标记字段（处理已有标记的情况）
        def combine_marks(row):
            marks = []
            if pd.notna(row[self.mark_field_name]):
                marks.append(row[self.mark_field_name])
            if pd.notna(row[f"{self.mark_field_name}_new"]):
                marks.append(row[f"{self.mark_field_name}_new"])
            if marks:
                return ';'.join(marks).replace('^;', '').strip(';')
            return np.nan

        if f"{self.mark_field_name}_new" in merged_df.columns:
            merged_df[self.mark_field_name] = merged_df.apply(combine_marks, axis=1)
            merged_df.drop(columns=[f"{self.mark_field_name}_new"], inplace=True)

        return merged_df

    def process(self, input_df: pd.DataFrame) -> pd.DataFrame:
        """
        主处理逻辑
        :param input_df: 输入DataFrame
        :return: 处理后的DataFrame
        """
        # 1. 验证字段存在性
        fields_to_monitor = list(self.fields_config.keys())
        missing_fields = [f for f in fields_to_monitor if f not in input_df.columns]
        if missing_fields:
            raise ValueError(f"Missing monitoring fields in data: {', '.join(missing_fields)}")

        if self.time_field not in input_df.columns:
            raise ValueError(f"Missing time field in data: {self.time_field}")

        # 2. 数据预处理
        df_prepared = self._prepare_data(input_df)

        # 3. 添加滞后值
        df_with_lags = self._add_lagged_values(df_prepared)

        # 4. 检测异常
        df_with_anomaly = self._detect_peak_anomaly(df_with_lags)

        # 5. 合并结果到原始数据
        result_df = self._merge_results(input_df, df_with_anomaly)

        # 清理临时列
        temp_cols = [col for col in result_df.columns if
                     col.endswith('_lag') or col.endswith('_temp') or col == 'consolidated_anomaly']
        result_df.drop(columns=temp_cols, errors='ignore', inplace=True)

        return result_df


def main():
    """
    命令行调用入口
    使用示例：
    python qc14_time_peak_value.py \
        --input_path /path/to/input.csv \
        --output_path /path/to/output.csv \
        --conditions "Do_ppm,1,3\nTemp_C,2,4\npH,4,5" \
        --time_field time \
        --time_format "%Y-%m-%d %H:%M:%S" \
        --qc_mark "尖值异常" \
        --mark_field_name QC0000
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='尖峰检验：连续剧烈变化检测')
    parser.add_argument('--input_path', required=True, help='输入文件路径')
    parser.add_argument('--output_path', required=True, help='输出文件路径')
    parser.add_argument('--conditions', required=True, help='峰值检验条件，格式：字段名,峰值阈值,连续次数（多行用\\n分隔）')
    parser.add_argument('--time_field', required=True, help='时间字段名')
    parser.add_argument('--time_format', required=True, help='时间格式，例如：%%Y-%%m-%%d %%H:%%M:%%S')
    parser.add_argument('--qc_mark', default='尖值异常', help='质控标识')
    parser.add_argument('--mark_field_name', default='QC0000', help='质控标识字段名')

    args = parser.parse_args()

    try:
        # 1. 读取输入数据
        print(f"Reading input data: {args.input_path}")
        input_df = data_io.read_structured_data(args.input_path)

        # 2. 初始化处理器并处理数据
        processor = QC14_TimePeakValue(
            conditions=args.conditions,
            time_field=args.time_field,
            time_format=args.time_format,
            qc_mark=args.qc_mark,
            mark_field_name=args.mark_field_name
        )
        print("Starting peak value check...")
        result_df = processor.process(input_df)

        # 3. 写入输出数据
        print(f"Writing output data: {args.output_path}")
        data_io.write_structured_data(result_df, args.output_path)

        print("Peak value check completed!")

    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()