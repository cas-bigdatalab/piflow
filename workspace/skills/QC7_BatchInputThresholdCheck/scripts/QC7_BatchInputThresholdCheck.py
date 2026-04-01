import argparse
import pandas as pd
from typing import Dict, Tuple
from data_io import read_structured_data, write_structured_data  # 导入data_io工具函数


class QC7_BatchInputThresholdCheck:
    """
    批量阈值检验-输入框：将数据列的值与输入阈值条件中定义的上下限进行比对，
    识别并标记超出允许范围（包括上限和下限）或为空值的数据点。
    """

    def __init__(self, conditions: str, qc_mark: str, mark_field_name: str = "QC0000"):
        """
        初始化参数
        :param conditions: 阈值检验条件，每行格式为 'field,max_value,min_value'
        :param qc_mark: 质控标识
        :param mark_field_name: 质控标识字段名，默认QC0000
        """
        self.conditions = conditions
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name
        self.thresholds_map: Dict[str, Tuple[float, float]] = self._parse_conditions()

    def _parse_conditions(self) -> Dict[str, Tuple[float, float]]:
        """解析阈值条件字符串为字典"""
        thresholds_map = {}
        lines = [line.strip() for line in self.conditions.split("\n") if line.strip()]

        for line in lines:
            parts = line.split(",")
            if len(parts) != 3:
                raise ValueError(f"无效的阈值行格式: {line}，预期格式为 'field,max,min'")

            field = parts[0].strip()
            try:
                max_val = float(parts[1].strip())
                min_val = float(parts[2].strip())
            except ValueError:
                raise ValueError(f"阈值必须为数字类型: {line}")

            # 确保max >= min
            if max_val < min_val:
                max_val, min_val = min_val, max_val
            thresholds_map[field] = (max_val, min_val)

        return thresholds_map

    def _check_field_invalid(self, df: pd.DataFrame) -> pd.DataFrame:
        """检查字段值是否超出阈值或为空，生成错误标记"""
        # 复制原数据避免修改
        df_copy = df.copy()
        error_columns = []

        # 为每个字段生成错误标记列
        for field, (max_val, min_val) in self.thresholds_map.items():
            if field not in df_copy.columns:
                raise ValueError(f"数据中不存在字段: {field}")

            # 转换为数值类型（处理空值）
            col_series = pd.to_numeric(df_copy[field], errors='coerce')

            # 判断是否无效：空值 或 超出上下限
            is_invalid = col_series.isnull() | (col_series > max_val) | (col_series < min_val)

            # 生成错误标记列（无效则为字段名，否则为空）
            error_col = df_copy.index.to_series().apply(lambda x: field if is_invalid[x] else "")
            error_columns.append(error_col)

        # 拼接所有错误字段名
        concat_errors = pd.Series([""] * len(df_copy))
        for col in error_columns:
            concat_errors = concat_errors + col + ","

        # 清理拼接结果（去除末尾逗号）
        concat_errors = concat_errors.str.rstrip(",").replace("", None)

        # 生成新的QC标记
        qc_new = concat_errors.apply(
            lambda x: f"{self.qc_mark}({x})" if x is not None else None
        )

        # 合并到原始QC字段
        self._merge_qc_field(df_copy, qc_new)

        return df_copy

    def _merge_qc_field(self, df: pd.DataFrame, qc_new: pd.Series):
        """将新生成的QC标记合并到原始QC字段"""
        # 初始化QC字段（如果不存在）
        if self.mark_field_name not in df.columns:
            df[self.mark_field_name] = None

        # 清理原始QC值和新QC值
        cleaned_original = df[self.mark_field_name].astype(str).replace({"nan": "", "None": ""}).str.strip()
        cleaned_new = qc_new.astype(str).replace({"nan": "", "None": ""}).str.strip()

        # 拼接逻辑：都有值则加分号，否则取非空值，都空则为None
        def concat_qc(original, new_val):
            if original and new_val:
                return f"{original};{new_val}"
            elif original:
                return original
            elif new_val:
                return new_val
            else:
                return None

        # 应用拼接逻辑
        df[self.mark_field_name] = [
            concat_qc(orig, new) for orig, new in zip(cleaned_original, cleaned_new)
        ]

    def process(self, input_path: str, output_path: str, **kwargs):
        """
        主处理逻辑
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        :param kwargs: 写入文件的额外参数（传递给write_structured_data）
        """
        # 读取数据
        df = read_structured_data(input_path)

        # 执行阈值检查
        result_df = self._check_field_invalid(df)

        # 写入结果
        write_structured_data(result_df, output_path, **kwargs)


def main():
    """命令行调用入口"""
    parser = argparse.ArgumentParser(description="批量阈值检验-输入框：检查数据列值是否超出阈值范围并标记")
    parser.add_argument("--input-path", required=True, help="输入文件路径")
    parser.add_argument("--output-path", required=True, help="输出文件路径")
    parser.add_argument("--conditions", required=True,
                        help="阈值检验条件，每行格式为'field,max_value,min_value'，多行用\\n分隔，示例：Temp,36,-5\\npH,14,0")
    parser.add_argument("--qc-mark", required=True, help="质控标识，示例：QC7")
    parser.add_argument("--mark-field-name", default="QC0000", help="质控标识字段名，默认QC0000")

    # 解析参数
    args = parser.parse_args()

    # 初始化处理器并执行
    processor = QC7_BatchInputThresholdCheck(
        conditions=args.conditions,
        qc_mark=args.qc_mark,
        mark_field_name=args.mark_field_name
    )
    processor.process(args.input_path, args.output_path)


if __name__ == "__main__":
    main()