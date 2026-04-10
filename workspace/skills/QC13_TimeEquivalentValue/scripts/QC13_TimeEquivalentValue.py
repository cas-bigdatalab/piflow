import argparse
import pandas as pd
from typing import Dict, List, Tuple
import data_io  # 导入结构化文件读写工具


class QC13_TimeEquivalentValue:
    """
    等值检验：连续数值无变化检查（久无变化检查）
    主要用于时间序列数据，在连续的时间段内，某个关键指标的数值长时间保持不变的情况
    """

    def __init__(self, conditions: str, time_field: str, time_format: str, qc_mark: str = "等值异常",
                 mark_field_name: str = "QC0000"):
        self.conditions = conditions
        self.time_field = time_field
        self.time_format = time_format
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name

        # 解析条件配置
        self.fields_config = self._parse_conditions()

    def _parse_conditions(self) -> Dict[str, int]:
        """
        解析条件字符串为字段名:连续次数的字典
        输入格式示例：Do_ppm,3\nTemp_C,3\npH,3
        """
        fields_config = {}
        if not self.conditions.strip():
            raise ValueError("Condition config cannot be empty")

        lines = self.conditions.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) != 2:
                raise ValueError(f"Invalid condition format, expected 'field_name,count': {line}")
            field_name, n_str = parts
            try:
                n = int(n_str)
                if n < 1:
                    raise ValueError(f"Continuous count must be >= 1: {line}")
                fields_config[field_name.strip()] = n
            except ValueError:
                raise ValueError(f"Continuous count must be an integer: {line}")
        return fields_config

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理：时间字段格式化、备份原始时间字段
        """
        # 检查时间字段是否存在
        if self.time_field not in df.columns:
            raise ValueError(f"Time field {self.time_field} not found in data")

        # 备份原始时间字段
        time_field_backup = f"{self.time_field}_origin_backup"
        df = df.copy()
        df[time_field_backup] = df[self.time_field]

        # 格式化时间字段
        try:
            df[self.time_field] = pd.to_datetime(df[self.time_field], format=self.time_format)
        except Exception as e:
            raise ValueError(f"Time field format failed, format: {self.time_format}, error: {str(e)}")

        # 检查监测字段是否存在
        missing_fields = [f for f in self.fields_config.keys() if f not in df.columns]
        if missing_fields:
            raise ValueError(f"Monitoring fields not found in data: {', '.join(missing_fields)}")

        # 按时间排序
        df = df.sort_values(by=self.time_field).reset_index(drop=True)
        return df

    def _detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        检测连续等值异常
        """
        df = self._prepare_data(df)
        time_field_backup = f"{self.time_field}_origin_backup"

        # 步骤1：为每个字段生成滞后列（前N-1个值）
        df_lagged = df.copy()
        for field, n in self.fields_config.items():
            if n <= 1:
                continue  # N=1时无需检测
            for i in range(1, n):
                df_lagged[f"{field}_lag{i}"] = df_lagged[field].shift(i)

        # 步骤2：生成每个字段的异常状态临时列
        temp_status_cols = []
        for field, n in self.fields_config.items():
            status_col = f"{field}_status_temp"
            temp_status_cols.append(status_col)

            if n <= 1:
                # N=1时无异常
                df_lagged[status_col] = None
                continue

            # 构建等值判断条件
            cond = df_lagged[field] == df_lagged[f"{field}_lag1"]
            for i in range(2, n):
                cond = cond & (df_lagged[field] == df_lagged[f"{field}_lag{i}"])

            # 异常时标记为字段名，否则为None
            df_lagged[status_col] = df_lagged[field].where(cond, None)

        # 步骤3：合并异常标记
        # 拼接所有异常字段名（逗号分隔）
        df_lagged['consolidated_anomaly'] = df_lagged[temp_status_cols].apply(
            lambda row: ','.join([str(x) for x in row if pd.notna(x)]), axis=1
        )

        # 生成最终质控标记
        df_lagged[self.mark_field_name] = df_lagged['consolidated_anomaly'].apply(
            lambda x: f"{self.qc_mark}({x})" if x else None
        )

        # 筛选有异常的记录，只保留时间备份和质控标记字段
        abnormal_df = df_lagged[[time_field_backup, self.mark_field_name]].dropna(subset=[self.mark_field_name])
        return abnormal_df

    def process(self, input_df: pd.DataFrame) -> pd.DataFrame:
        """
        主处理逻辑：检测异常并合并到原始数据
        """
        # 移除原始数据中的质控标记列（如果存在）
        input_df_clean = input_df.drop(columns=[self.mark_field_name], errors='ignore')

        # 检测异常
        abnormal_df = self._detect_anomalies(input_df_clean)
        time_field_backup = f"{self.time_field}_origin_backup"

        # 合并异常标记到原始数据
        result_df = input_df_clean.merge(
            abnormal_df,
            left_on=self.time_field,
            right_on=time_field_backup,
            how='left'
        )

        # 处理原有质控标记和新标记的拼接（如果原始数据已有质控标记）
        if self.mark_field_name in input_df.columns:
            # 合并原有标记和新标记
            result_df[self.mark_field_name] = result_df.apply(
                lambda row: ';'.join(
                    filter(None, [row[f"{self.mark_field_name}_x"], row[f"{self.mark_field_name}_y"]])),
                axis=1
            )
            # 删除临时列
            result_df = result_df.drop(columns=[f"{self.mark_field_name}_x", f"{self.mark_field_name}_y"])

        # 删除时间备份列
        result_df = result_df.drop(columns=[time_field_backup], errors='ignore')

        return result_df


def main():
    """
    命令行调用入口
    使用示例：
    python qc13_time_equivalent_value.py \
        --input_path /path/to/input.csv \
        --output_path /path/to/output.csv \
        --conditions "Do_ppm,3\nTemp_C,3\npH,3" \
        --time_field time \
        --time_format "%Y-%m-%d %H:%M:%S" \
        --qc_mark "等值异常" \
        --mark_field_name QC0000
    """
    # 构建命令行参数解析器
    parser = argparse.ArgumentParser(description="等值检验：连续数值无变化检查")
    parser.add_argument('--input_path', required=True, help='输入文件路径（支持csv/parquet等结构化格式）')
    parser.add_argument('--output_path', required=True, help='输出文件路径（支持csv/parquet等结构化格式）')
    parser.add_argument('--conditions', required=True, help='等值检验条件，格式：字段名,连续次数\\n字段名,连续次数')
    parser.add_argument('--time_field', required=True, help='时间字段名（用于排序判断连续性）')
    parser.add_argument('--time_format', required=True, help='时间格式，例如：%%Y-%%m-%%d %%H:%%M:%%S')
    parser.add_argument('--qc_mark', default='等值异常', help='质控标识（默认：等值异常）')
    parser.add_argument('--mark_field_name', default='QC0000', help='质控标识字段名（默认：QC0000）')

    # 解析参数
    args = parser.parse_args()

    try:
        # 1. 读取输入数据（使用data_io）
        print(f"Reading input data: {args.input_path}")
        input_df = data_io.read_structured_data(args.input_path)

        # 2. 初始化并执行质控检查
        qc_processor = QC13_TimeEquivalentValue(
            conditions=args.conditions,
            time_field=args.time_field,
            time_format=args.time_format,
            qc_mark=args.qc_mark,
            mark_field_name=args.mark_field_name
        )
        result_df = qc_processor.process(input_df)

        # 3. 写入输出数据（使用data_io）
        print(f"Writing output data: {args.output_path}")
        data_io.write_structured_data(result_df, args.output_path)

        print("Processing completed!")

    except Exception as e:
        print(f"Processing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()