import argparse
import pandas as pd
from typing import Optional
# 假设data_io.py在同级目录，需确保该文件存在且包含指定的读写方法
from data_io import read_structured_data, write_structured_data


class QC10_TimeConsistency:
    """时间一致性检查"""

    def __init__(self, field_name: str, range_of_change: str, change_type: str,
                 qc_mark: str, mark_field_name: str = "QC0000", id_field_name: str = "ID0000"):
        self.field_name = field_name
        self.range_of_change = float(range_of_change)
        self.change_type = change_type  # 正值/负值/绝对值
        self.QcMark = qc_mark
        self.mark_field_name = mark_field_name
        self.id_field_name = id_field_name

        # 分组字段和排序字段（对应原Scala中的固定值）
        self.group_fields = ["sss000", "sscode", "fa0110", "fa0112"]
        self.order_field = "yyyy00"

    def perform(self, input_path: str, origin_output_path: str, error_output_path: Optional[str] = None):
        """
        核心处理逻辑
        :param input_path: 输入文件路径
        :param origin_output_path: 处理后正常数据输出路径
        :param error_output_path: 异常数据输出路径（可选）
        """
        # 1. 读取输入数据
        df = read_structured_data(input_path)

        # 2. 数据预处理：按分组字段分区，排序字段排序并添加rank
        # 先检查必要字段是否存在
        required_fields = self.group_fields + [self.order_field, self.field_name, self.id_field_name]
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            raise ValueError(f"数据缺失必要字段: {missing_fields}")

        # 移除原有标记字段（如果存在）
        if self.mark_field_name in df.columns:
            df = df.drop(columns=[self.mark_field_name])

        # 按分组字段排序并添加rank
        df_sorted = df.sort_values(by=self.group_fields + [self.order_field], ascending=True)
        df_sorted["rank"] = df_sorted.groupby(self.group_fields).cumcount() + 1  # 从1开始计数，对应原rank

        # 3. 关联上一条记录，计算异常标记
        # 自关联：a.rank = b.rank + 1
        df_a = df_sorted.rename(columns={col: f"a_{col}" for col in df_sorted.columns})
        df_b = df_sorted.rename(columns={col: f"b_{col}" for col in df_sorted.columns})
        df_b["b_rank_plus_1"] = df_b["b_rank"] + 1

        # 关联条件：分组字段相等 + a.rank = b.rank + 1
        join_conditions = [df_a[f"a_{f}"] == df_b[f"b_{f}"] for f in self.group_fields] + [
            df_a["a_rank"] == df_b["b_rank_plus_1"]]
        df_join = pd.merge(df_a, df_b, on=None, how="left", left_on=None, right_on=None,
                           suffixes=("", ""), condition=lambda x: all(join_conditions))

        # 计算年差值绝对值
        df_join["a_yyyy00_int"] = df_join["a_yyyy00"].astype(int)
        df_join["b_yyyy00_int"] = df_join["b_yyyy00"].astype(int)
        df_join["annual_mean"] = abs(df_join["a_yyyy00_int"] - df_join["b_yyyy00_int"])

        # 计算字段差值
        df_join["a_field"] = df_join[f"a_{self.field_name}"].astype(float)
        df_join["b_field"] = df_join[f"b_{self.field_name}"].astype(float)
        df_join["field_diff"] = df_join["a_field"] - df_join["b_field"]

        # 根据变化类型判断异常
        if self.change_type == "正值":
            condition = df_join["field_diff"] > self.range_of_change * df_join["annual_mean"]
        elif self.change_type == "负值":
            condition = df_join["field_diff"] < -self.range_of_change * df_join["annual_mean"]
        else:  # 绝对值
            condition = abs(df_join["field_diff"]) > self.range_of_change * df_join["annual_mean"]

        # 添加异常标记
        df_join[self.mark_field_name] = df_join.apply(
            lambda row: self.QcMark if condition[row.name] else None, axis=1
        )

        # 提取异常数据
        abnormal_df = df_join[df_join[self.mark_field_name].notna()].copy()
        # 还原原始字段名（去掉a_前缀）
        abnormal_df = abnormal_df.rename(columns={f"a_{col}": col for col in df.columns})
        abnormal_df = abnormal_df.drop(columns=[col for col in abnormal_df.columns if
                                                col.startswith("b_") or col in ["rank", "annual_mean", "field_diff",
                                                                                "a_yyyy00_int", "b_yyyy00_int",
                                                                                "b_rank_plus_1"]])

        # 4. 合并原始数据和异常标记
        # 先确保原始数据的id字段唯一
        if df[self.id_field_name].duplicated().any():
            raise ValueError(f"唯一ID字段 {self.id_field_name} 存在重复值")

        # 左连接异常数据，合并标记
        abnormal_id_df = abnormal_df[[self.id_field_name, self.mark_field_name]].copy()
        df_origin = df.copy()
        if self.mark_field_name not in df_origin.columns:
            df_origin[self.mark_field_name] = ""

        # 合并标记逻辑：原标记 + 新标记，用;分隔，去除开头的;
        df_out = pd.merge(df_origin, abnormal_id_df, on=self.id_field_name, how="left", suffixes=("", "_new"))
        df_out["mark_combined"] = df_out[self.mark_field_name] + ";" + df_out[f"{self.mark_field_name}_new"].fillna("")
        df_out["mark_combined"] = df_out["mark_combined"].str.lstrip(";").str.rstrip(";")
        df_out = df_out.drop(columns=[self.mark_field_name, f"{self.mark_field_name}_new"])
        df_out[self.mark_field_name] = df_out["mark_combined"]
        df_out = df_out.drop(columns=["mark_combined"])

        # 5. 写入输出文件
        write_structured_data(df_out, origin_output_path)
        if error_output_path and not abnormal_df.empty:
            write_structured_data(abnormal_df, error_output_path)

        # 打印异常信息（可选）
        if not abnormal_df.empty:
            print("########## Exception: Time consistency check failed!!!")
            print(f"Abnormal data count: {len(abnormal_df)}")
            print("First 10 abnormal records:")
            print(abnormal_df.head(10))


def main():
    """
    命令行调用入口函数
    示例调用：
    python qc10_time_consistency.py \
        --input_path /path/to/input.csv \
        --origin_output_path /path/to/output.csv \
        --error_output_path /path/to/error.csv \
        --field_name "胸径" \
        --range_of_change 0.5 \
        --change_type "绝对值" \
        --qc_mark "QC10" \
        --mark_field_name "QC0000" \
        --id_field_name "ID0000"
    """
    parser = argparse.ArgumentParser(description="时间一致性检查(胸径树高)")
    # 文件路径参数
    parser.add_argument("--input_path", required=True, type=str, help="输入文件路径")
    parser.add_argument("--origin_output_path", required=True, type=str, help="处理后数据输出路径")
    parser.add_argument("--error_output_path", type=str, default=None, help="异常数据输出路径（可选）")

    # 核心参数
    parser.add_argument("--field_name", required=True, type=str, help="一致性检查字段名")
    parser.add_argument("--range_of_change", required=True, type=str, help="年变化量")
    parser.add_argument("--change_type", required=True, type=str, choices=["正值", "负值", "绝对值"],
                        default="绝对值", help="变化类型（正值为增加量，负值为减小量，绝对值为正负变化量）")
    parser.add_argument("--qc_mark", required=True, type=str, help="质控标识")
    parser.add_argument("--mark_field_name", type=str, default="QC0000", help="质控标识字段名")
    parser.add_argument("--id_field_name", type=str, default="ID0000", help="唯一ID字段名")

    # 解析参数
    args = parser.parse_args()

    # 初始化检查类并执行处理
    qc_checker = QC10_TimeConsistency(
        field_name=args.field_name,
        range_of_change=args.range_of_change,
        change_type=args.change_type,
        qc_mark=args.qc_mark,
        mark_field_name=args.mark_field_name,
        id_field_name=args.id_field_name
    )

    # 执行核心逻辑
    qc_checker.perform(
        input_path=args.input_path,
        origin_output_path=args.origin_output_path,
        error_output_path=args.error_output_path
    )


if __name__ == "__main__":
    main()