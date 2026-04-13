import argparse
import pandas as pd
from datetime import datetime, timedelta
import data_io


class QC16_TimeMissing:
    """
    Data time sequence completeness check: detect missing and extra data points;
    Set data recording frequency (e.g., every 2, 30 or 60 minutes), use this frequency as base to traverse data time range, check if data time sequence is complete
    """

    def __init__(self, data_frequency: str, time_field: str, time_format: str, mark_field_name: str):
        """
        Initialize parameters
        :param data_frequency: Data frequency (minutes, e.g., "30" means 30 minutes)
        :param time_field: Time field name
        :param time_format: Time field format (e.g., "yyyy-MM-dd HH:mm:ss")
        :param mark_field_name: QC mark field name
        """
        self.data_frequency = int(data_frequency)
        self.time_field = time_field
        self.time_format = time_format
        self.mark_field_name = mark_field_name

    def process(self, input_df: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        """
        Core processing logic: check missing and extra time points
        :param input_df: Input data DataFrame
        :return: Original data DF, error data DF (missing + extra time points)
        """
        df_process = input_df.copy()
        try:
            df_process[self.time_field] = pd.to_datetime(df_process[self.time_field], format=self.time_format)
        except Exception as e:
            raise ValueError(f"Time field conversion failed, please check if time format is correct: {e}")

        min_timestamp = df_process[self.time_field].min()
        max_timestamp = df_process[self.time_field].max()
        print(f"Min timestamp in data: {min_timestamp}")
        print(f"Max timestamp in data: {max_timestamp}")

        interval_seconds = self.data_frequency * 60
        total_duration_seconds = (max_timestamp - min_timestamp).total_seconds()
        num_intervals = int(total_duration_seconds / interval_seconds) + 1

        expected_timestamps = []
        current_ts = min_timestamp
        for _ in range(num_intervals):
            expected_timestamps.append(current_ts)
            current_ts += timedelta(seconds=interval_seconds)
        full_time_range_df = pd.DataFrame({
            "expected_timestamp": expected_timestamps
        })

        df_process_ts = df_process[[self.time_field]].copy()
        df_process_ts[self.time_field] = pd.to_datetime(df_process_ts[self.time_field])
        full_time_range_df["expected_timestamp"] = pd.to_datetime(full_time_range_df["expected_timestamp"])

        missing_timestamps_df = full_time_range_df[
            ~full_time_range_df["expected_timestamp"].isin(df_process_ts[self.time_field])
        ].rename(columns={"expected_timestamp": self.time_field})
        missing_timestamps_df[self.mark_field_name] = "Missing time point"

        print("\n--- Missing time period check report ---")
        if missing_timestamps_df.empty:
            print("No missing time periods found under specified frequency.")
        else:
            print(f"Found missing time periods, total {len(missing_timestamps_df)} time points:")

        extra_timestamps_df = df_process_ts[
            ~df_process_ts[self.time_field].isin(full_time_range_df["expected_timestamp"])
        ].copy()
        extra_timestamps_df[self.mark_field_name] = "Extra time point"

        print("\n--- Extra/mismatched time period check report ---")
        if extra_timestamps_df.empty:
            print("No extra or mismatched time points found with expected frequency.")
        else:
            print(f"Found extra/mismatched time periods, total {len(extra_timestamps_df)} time points:")

        error_df = pd.concat([missing_timestamps_df, extra_timestamps_df], ignore_index=True)
        error_df = error_df.sort_values(
            by=[self.mark_field_name, self.time_field],
            ascending=[False, True],
            ignore_index=True
        )

        return input_df, error_df


def main():
    """
    Command line entry point: support specifying input/output paths and necessary parameters
    Usage example:
    python QC16_TimeMissing.py \
        --input_path /path/to/input.csv \
        --origin_output_path /path/to/origin_output.csv \
        --error_output_path /path/to/error_output.csv \
        --data_frequency 30 \
        --time_field time \
        --time_format "%Y-%m-%d %H:%M:%S" \
        --mark_field_name QC0000
    """
    parser = argparse.ArgumentParser(description="Data time sequence completeness check tool")
    parser.add_argument("--input_path", required=True, type=str, help="Input data file path")
    parser.add_argument("--origin_output_path", required=True, type=str, help="Original data output path")
    parser.add_argument("--error_output_path", required=True, type=str, help="Error data (missing/extra time points) output path")
    parser.add_argument("--data_frequency", required=True, type=str, help="Data frequency (minutes, e.g., 30 means 30 minutes)")
    parser.add_argument("--time_field", required=True, type=str, help="Time field name (e.g., time)")
    parser.add_argument("--time_format", required=True, type=str, help="Time format (e.g., %%Y-%%m-%%d %%H:%%M:%%S)")
    parser.add_argument("--mark_field_name", required=True, type=str, help="QC mark field name (e.g., QC0000)")

    args = parser.parse_args()

    try:
        print("Start reading input data...")
        input_df = data_io.read_structured_data(args.input_path)

        processor = QC16_TimeMissing(
            data_frequency=args.data_frequency,
            time_field=args.time_field,
            time_format=args.time_format,
            mark_field_name=args.mark_field_name
        )
        origin_df, error_df = processor.process(input_df)

        print("Start writing original data...")
        data_io.write_structured_data(origin_df, args.origin_output_path)
        print("Start writing error data...")
        data_io.write_structured_data(error_df, args.error_output_path)

        print("Processing completed!")

    except Exception as e:
        print(f"Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()
