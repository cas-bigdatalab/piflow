import argparse
import pandas as pd
from typing import Dict, Tuple
# 导入data_io模块中的读写函数
from data_io import read_structured_data, write_structured_data


class QC5BatchThresholdCheck:
    """
    批量阈值检验-阈值表：将数据列的值与阈值表中定义的上下限进行比对，
    识别并标记超出允许范围（包括上限和下限）或为空值的数据点；
    阈值表的结构必须包括【field,min_value,max_value】字段
    """

    def __init__(self, qc_mark: str, mark_field_name: str = "QC0000"):
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name

    def process(self, original_data_path: str, threshold_data_path: str, output_path: str):
        """
        核心处理逻辑
        :param original_data_path: 原始数据文件路径
        :param threshold_data_path: 阈值表文件路径
        :param output_path: 处理后数据输出路径
        """
        # 1. 读取原始数据和阈值表数据
        df_original = read_structured_data(original_data_path)
        df_thresholds = read_structured_data(threshold_data_path)

        # 2. 构建阈值映射表：{字段名: (最大值, 最小值)}
        thresholds_map: Dict[str, Tuple[float, float]] = {}
        for _, row in df_thresholds.iterrows():
            field = row["field"]
            max_val = row["max_value"]
            min_val = row["min_value"]
            thresholds_map[field] = (max_val, min_val)

        # 3. 初始化新的质控列（如果不存在则创建）
        if self.mark_field_name not in df_original.columns:
            df_original[self.mark_field_name] = None

        # 4. 遍历每个字段，判断是否超出阈值或为空
        def get_error_fields(row) -> str:
            """判断单行数据的错误字段"""
            error_fields = []
            for field, (max_val, min_val) in thresholds_map.items():
                # 处理字段不存在或值为空的情况
                if field not in row.index or pd.isna(row[field]):
                    error_fields.append(field)
                    continue

                # 转换为数值类型（兼容字符串格式的数值）
                try:
                    val = float(row[field])
                except (ValueError, TypeError):
                    error_fields.append(field)
                    continue

                # 判断是否超出阈值范围
                if val > max_val or val < min_val:
                    error_fields.append(field)

            return ",".join(error_fields) if error_fields else ""

        # 5. 计算每行的新质控标记
        df_original["_temp_new_qc"] = df_original.apply(get_error_fields, axis=1)

        # 6. 构建新的质控字符串
        def build_qc_string(row) -> str:
            original_qc = str(row[self.mark_field_name]).strip() if pd.notna(row[self.mark_field_name]) else ""
            new_qc = row["_temp_new_qc"]

            # 构建新质控标记
            new_qc_str = f"{self.qc_mark}({new_qc})" if new_qc else ""

            # 拼接逻辑：原始和新标记都有值时用分号分隔
            if original_qc and new_qc_str:
                return f"{original_qc};{new_qc_str}"
            elif original_qc:
                return original_qc
            elif new_qc_str:
                return new_qc_str
            else:
                return None

        # 7. 更新质控字段
        df_original[self.mark_field_name] = df_original.apply(build_qc_string, axis=1)

        # 8. 删除临时列
        df_original = df_original.drop(columns=["_temp_new_qc"])

        # 9. 写入输出文件
        write_structured_data(df_original, output_path)


def main():
    """
    命令行调用入口函数
    示例调用指令：
    python QC5_BatchThresholdCheck.py \
        --original_data_path /path/to/original.csv \
        --threshold_data_path /path/to/threshold.csv \
        --output_path /path/to/output.csv \
        --qc_mark "QC5" \
        --mark_field_name "QC0000"
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="批量阈值检验工具")
    parser.add_argument("--original_data_path", required=True, help="原始数据文件路径")
    parser.add_argument("--threshold_data_path", required=True, help="阈值表文件路径")
    parser.add_argument("--output_path", required=True, help="处理后数据输出路径")
    parser.add_argument("--qc_mark", required=True, help="质控标识（如QC5）")
    parser.add_argument("--mark_field_name", default="QC0000", help="质控标识字段名，默认QC0000")

    args = parser.parse_args()

    # 初始化并执行处理逻辑
    qc_processor = QC5BatchThresholdCheck(
        qc_mark=args.qc_mark,
        mark_field_name=args.mark_field_name
    )
    qc_processor.process(
        original_data_path=args.original_data_path,
        threshold_data_path=args.threshold_data_path,
        output_path=args.output_path
    )

    print(f"Processing completed! Output saved to: {args.output_path}")


if __name__ == "__main__":
    main()