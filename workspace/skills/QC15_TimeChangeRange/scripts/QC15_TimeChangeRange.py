import argparse
import pandas as pd
from typing import Dict, Tuple, List
import data_io  # 导入结构化文件读写工具


class QC15_TimeChangeRange:
    """
    最大变化范围检验：主要用于时间序列数据；
    在特定时间窗口内，数据是否出现了异常剧烈波动，即在任意两个读数之间，其差值（变化量）的绝对值超出了预设的容忍阈值
    """

    def __init__(self):
        self.conditions: str = ""
        self.time_field: str = ""
        self.time_format: str = ""
        self.qc_mark: str = "最大变化范围检验异常"
        self.mark_field_name: str = "QC0000"

    def parse_conditions(self) -> Dict[str, Tuple[float, int]]:
        """
        解析条件字符串为字段配置字典
        输入格式示例：Do_ppm,1,3\nTemp_C,2,4\npH,4,5\nSal,3,4
        返回格式：{字段名: (阈值lift, 连续次数N)}
        """
        config_dict = {}
        if not self.conditions.strip():
            raise ValueError("No condition config provided, please check input")

        lines = self.conditions.strip().split("\n")
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) != 3:
                raise ValueError(f"Invalid condition format: {line}, expected: field_name,threshold,count")

            field = parts[0].strip()
            try:
                lift = float(parts[1].strip())
                n = int(parts[2].strip())
            except ValueError:
                raise ValueError(f"Invalid condition value format: {line}, threshold should be float, count should be integer")

            config_dict[field] = (lift, n)
        return config_dict

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理：时间字段转换、备份原始时间字段
        """
        # 备份原始时间字段
        time_field_backup = f"{self.time_field}_origin_backup"
        df = df.copy()
        df[time_field_backup] = df[self.time_field]

        # 转换时间字段为datetime类型
        try:
            df[self.time_field] = pd.to_datetime(df[self.time_field], format=self.time_format)
        except Exception as e:
            raise ValueError(f"Time field conversion failed: {e}")

        # 按时间字段排序
        df = df.sort_values(by=self.time_field).reset_index(drop=True)

        return df

    def calculate_window_min_max(self, df: pd.DataFrame, fields_config: Dict[str, Tuple[float, int]]) -> pd.DataFrame:
        """
        为每个监测字段计算滑动窗口内的最大值和最小值
        """
        df = df.copy()
        fields_to_monitor = fields_config.keys()

        for field in fields_to_monitor:
            lift, n = fields_config[field]

            # 计算滑动窗口的最大/最小值（向前n-1行到当前行）
            window_spec = f"{n}T" if n > 0 else "1T"
            df[f"{field}_window_max"] = df[field].rolling(window=n, min_periods=1).max()
            df[f"{field}_window_min"] = df[field].rolling(window=n, min_periods=1).min()

        return df

    def mark_anomaly_status(self, df: pd.DataFrame, fields_config: Dict[str, Tuple[float, int]]) -> pd.DataFrame:
        """
        标记每个字段的异常状态
        """
        df = df.copy()
        fields_to_monitor = fields_config.keys()
        temp_anomaly_cols = []

        for field in fields_to_monitor:
            lift, n = fields_config[field]
            temp_col = f"{field}_status_temp"
            temp_anomaly_cols.append(temp_col)

            # 构建异常判断条件
            window_max = df[f"{field}_window_max"]
            window_min = df[f"{field}_window_min"]
            field_val = df[field]

            # 异常条件：最大值-最小值 >= 阈值，且字段值非空
            anomaly_mask = (
                    window_max.notna() &
                    window_min.notna() &
                    field_val.notna() &
                    (window_max - window_min >= lift)
            )

            # 标记异常字段名，否则为None
            df[temp_col] = df[temp_col].where(~anomaly_mask, field)
            df[temp_col] = df[temp_col].where(anomaly_mask, None)

        # 合并所有异常标记
        df["consolidated_anomaly"] = df[temp_anomaly_cols].apply(
            lambda row: ",".join([str(x) for x in row if x is not None]), axis=1
        )

        # 生成最终质控标记字段
        df[self.mark_field_name] = df["consolidated_anomaly"].apply(
            lambda x: f"{self.qc_mark}({x})" if x else None
        )

        return df

    def merge_results(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> pd.DataFrame:
        """
        合并原始数据和异常标记结果
        """
        # 只保留需要的列用于合并
        time_field_backup = f"{self.time_field}_origin_backup"
        abnormal_df = processed_df[[time_field_backup, self.mark_field_name]].copy()
        abnormal_df = abnormal_df[abnormal_df[self.mark_field_name].notna()]

        # 左连接原始数据和异常标记
        merged_df = original_df.merge(
            abnormal_df,
            left_on=self.time_field,
            right_on=time_field_backup,
            how="left",
            suffixes=("", "_new")
        )

        # 合并质控标记字段
        if f"{self.mark_field_name}_new" in merged_df.columns:
            merged_df[self.mark_field_name] = merged_df.apply(
                lambda row: ";".join([
                    str(x) for x in [row[self.mark_field_name], row[f"{self.mark_field_name}_new"]]
                    if x is not None and str(x).strip()
                ]),
                axis=1
            )

            # 移除临时列
            merged_df = merged_df.drop(columns=[time_field_backup, f"{self.mark_field_name}_new"])

        # 清理空值
        merged_df[self.mark_field_name] = merged_df[self.mark_field_name].replace("", None)

        return merged_df

    def process(self, input_path: str, output_path: str):
        """
        主处理逻辑：读取数据 -> 检验 -> 输出结果
        """
        # 1. 读取输入数据
        print(f"Reading input data: {input_path}")
        df = data_io.read_structured_data(input_path)

        # 2. 验证必要字段存在
        fields_config = self.parse_conditions()
        fields_to_monitor = fields_config.keys()

        # 检查时间字段是否存在
        if self.time_field not in df.columns:
            raise ValueError(f"Time field not found in data: {self.time_field}")

        # 检查监测字段是否存在
        missing_fields = [f for f in fields_to_monitor if f not in df.columns]
        if missing_fields:
            raise ValueError(f"Monitoring fields not found in data: {', '.join(missing_fields)}")

        # 3. 数据预处理
        df_prepared = self.prepare_data(df)

        # 4. 计算窗口极值
        df_with_min_max = self.calculate_window_min_max(df_prepared, fields_config)

        # 5. 标记异常状态
        df_with_anomaly = self.mark_anomaly_status(df_with_min_max, fields_config)

        # 6. 合并结果
        final_df = self.merge_results(df, df_with_anomaly)

        # 7. 输出结果
        print(f"Writing output data: {output_path}")
        data_io.write_structured_data(final_df, output_path)
        print("Processing completed!")


def main():
    """
    命令行调用入口函数
    使用示例：
    python qc15_time_change_range.py \
        --input_path /path/to/input.csv \
        --output_path /path/to/output.csv \
        --conditions "Do_ppm,1,3\nTemp_C,2,4\npH,4,5" \
        --time_field time \
        --time_format "%Y-%m-%d %H:%M:%S" \
        --qc_mark "最大变化范围检验异常" \
        --mark_field_name QC0000
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="最大变化范围检验脚本（QC15）")

    # 添加命令行参数
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--conditions", required=True,
                        help="变化范围检验条件：字段名,峰值,连续次数，多行用\\n分隔，示例：Do_ppm,1,3\\nTemp_C,2,4")
    parser.add_argument("--time_field", required=True, help="时间字段名，例如：time")
    parser.add_argument("--time_format", required=True,
                        help="时间格式，例如：%%Y-%%m-%%d %%H:%%M:%%S（命令行中需要双百分号）")
    parser.add_argument("--qc_mark", default="最大变化范围检验异常", help="质控标识")
    parser.add_argument("--mark_field_name", default="QC0000", help="质控标识字段名")

    # 解析参数
    args = parser.parse_args()

    # 初始化并运行检验逻辑
    qc_processor = QC15_TimeChangeRange()
    qc_processor.conditions = args.conditions
    qc_processor.time_field = args.time_field
    qc_processor.time_format = args.time_format
    qc_processor.qc_mark = args.qc_mark
    qc_processor.mark_field_name = args.mark_field_name

    # 执行处理
    try:
        qc_processor.process(args.input_path, args.output_path)
    except Exception as e:
        print(f"Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()