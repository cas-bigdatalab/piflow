import argparse
import pandas as pd
from data_io import read_structured_data, write_structured_data


class QC2_EnumerationFieldCheck:
    """
    公共基础项枚举校验: 生态站代码、样地代码、物种名称、样方号、树号等枚举校验
    将被检验表中的属性项值与相应标准词典进行比对，检查是否超出词典规定的固有词表枚举值范围
    """

    def __init__(self, comparison_field: str, qc_mark: str, mark_field_name: str, id_field_name: str):
        """
        初始化枚举校验类
        :param comparison_field: 枚举值检测对比字段,以冒号分隔，示例："sscode,ssname:sscode,ssname"
        :param qc_mark: 质控标识
        :param mark_field_name: 质控标识字段名
        :param id_field_name: 唯一ID字段名
        """
        self.comparison_field = comparison_field
        self.qc_mark = qc_mark
        self.mark_field_name = mark_field_name
        self.id_field_name = id_field_name

    def perform(self, origin_file_path: str, standard_file_path: str, error_output_path: str, origin_output_path: str):
        """
        执行枚举校验逻辑
        :param origin_file_path: 原始数据文件路径
        :param standard_file_path: 标准词典文件路径
        :param error_output_path: 异常数据输出路径
        :param origin_output_path: 处理后原始数据输出路径
        """
        # 读取输入数据
        origin_df = read_structured_data(origin_file_path)
        standard_df = read_structured_data(standard_file_path)

        # 处理对比字段
        origin_fields_str, standard_fields_str = self.comparison_field.split(":")
        origin_fields = [field.strip() for field in origin_fields_str.split(",")]
        standard_fields = [field.strip() for field in standard_fields_str.split(",")]

        # 校验字段是否存在
        self._check_fields_exist(origin_df, origin_fields, "原始数据")
        self._check_fields_exist(standard_df, standard_fields, "标准词典")

        # 去除两端空格
        for field in origin_fields:
            origin_df[field] = origin_df[field].astype(str).str.strip()
        for field in standard_fields:
            standard_df[field] = standard_df[field].astype(str).str.strip()

        # 构建匹配条件，合并多字段匹配
        merge_keys = []
        for i, (ori_field, std_field) in enumerate(zip(origin_fields, standard_fields)):
            # 为临时合并列命名
            temp_key = f"temp_merge_key_{i}"
            origin_df[temp_key] = origin_df[ori_field]
            standard_df[temp_key] = standard_df[std_field]
            merge_keys.append(temp_key)

        # 找出原始数据中不在标准词典中的异常数据
        # 先获取标准词典的唯一组合
        standard_comb = standard_df[merge_keys].drop_duplicates()
        # 关联原始数据和标准词典，找出不匹配的行
        merged_df = origin_df.merge(
            standard_comb,
            on=merge_keys,
            how="left",
            indicator=True
        )
        abnormal_df = origin_df[merged_df["_merge"] == "left_only"].copy()

        # 添加质控标识
        if self.mark_field_name in abnormal_df.columns:
            abnormal_df = abnormal_df.drop(columns=[self.mark_field_name])
        abnormal_df[self.mark_field_name] = self.qc_mark

        # 处理原始数据的质控标识字段
        origin_df_copy = origin_df.copy()
        # 左连接异常数据，更新质控标识
        abnormal_id_df = abnormal_df[[self.id_field_name, self.mark_field_name]]
        merged_origin_df = origin_df_copy.merge(
            abnormal_id_df,
            on=self.id_field_name,
            how="left",
            suffixes=("", "_abnormal")
        )

        # 构建新的质控标识字段
        def concat_qc_mark(row):
            original_mark = row[self.mark_field_name] if pd.notna(row[self.mark_field_name]) else ""
            abnormal_mark = row[f"{self.mark_field_name}_abnormal"] if pd.notna(row[f"{self.mark_field_name}_abnormal"]) else ""
            combined = ";".join([original_mark, abnormal_mark]).strip(";")
            return combined if combined else None

        merged_origin_df[self.mark_field_name] = merged_origin_df.apply(concat_qc_mark, axis=1)
        # 删除临时列
        merged_origin_df = merged_origin_df.drop(columns=[f"{self.mark_field_name}_abnormal"] + merge_keys)
        # 删除origin_df中的临时列
        origin_df = origin_df.drop(columns=merge_keys)
        # 删除abnormal_df中的临时列
        abnormal_df = abnormal_df.drop(columns=merge_keys)

        # 排序并输出异常数据
        if not abnormal_df.empty:
            abnormal_df = abnormal_df.sort_values(by=self.id_field_name)

        # 写入输出文件
        write_structured_data(abnormal_df, error_output_path)
        write_structured_data(merged_origin_df, origin_output_path)

        # 打印异常信息（可选）
        if not abnormal_df.empty:
            print("########## Exception: Enumeration value out of range!!!")
            print(f"Abnormal data (first 10 rows):")
            print(abnormal_df.head(10).to_string())

    def _check_fields_exist(self, df: pd.DataFrame, fields: list, df_name: str):
        """
        检查字段是否存在于DataFrame中
        :param df: 待检查的DataFrame
        :param fields: 需要检查的字段列表
        :param df_name: DataFrame名称（用于错误提示）
        """
        missing_fields = [field for field in fields if field not in df.columns]
        if missing_fields:
            raise ValueError(f"Missing required fields in {df_name}: {', '.join(missing_fields)}")


def main():
    """
    命令行调用入口函数
    示例调用：
    python QC2_EnumerationFieldCheck.py \
        --origin_file_path /path/to/origin.csv \
        --standard_file_path /path/to/standard.csv \
        --error_output_path /path/to/error.csv \
        --origin_output_path /path/to/output.csv \
        --comparison_field "sscode,ssname:sscode,ssname" \
        --qc_mark "QC2_ERROR" \
        --mark_field_name "QC0000" \
        --id_field_name "ID0000"
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="公共基础项枚举校验工具")
    # 文件路径参数
    parser.add_argument("--origin_file_path", required=True, help="原始数据文件路径")
    parser.add_argument("--standard_file_path", required=True, help="标准词典文件路径")
    parser.add_argument("--error_output_path", required=True, help="异常数据输出路径")
    parser.add_argument("--origin_output_path", required=True, help="处理后原始数据输出路径")
    # 业务参数
    parser.add_argument("--comparison_field", required=True,
                        help="枚举值检测对比字段,以冒号分隔，示例：sscode,ssname:sscode,ssname")
    parser.add_argument("--qc_mark", required=True, help="质控标识")
    parser.add_argument("--mark_field_name", required=True, default="QC0000",
                        help="质控标识字段名（默认：QC0000）")
    parser.add_argument("--id_field_name", required=True, default="ID0000",
                        help="唯一ID字段名（默认：ID0000）")

    # 解析参数
    args = parser.parse_args()

    # 初始化校验类并执行
    qc_checker = QC2_EnumerationFieldCheck(
        comparison_field=args.comparison_field,
        qc_mark=args.qc_mark,
        mark_field_name=args.mark_field_name,
        id_field_name=args.id_field_name
    )

    # 执行校验逻辑
    try:
        qc_checker.perform(
            origin_file_path=args.origin_file_path,
            standard_file_path=args.standard_file_path,
            error_output_path=args.error_output_path,
            origin_output_path=args.origin_output_path
        )
        print("Enumeration check completed, output files generated!")
    except Exception as e:
        print(f"Enumeration check failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()