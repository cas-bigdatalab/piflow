package cn.piflow

import cn.piflow.util.SciDataFrame
import org.apache.spark.sql.DataFrame

object SciDataFrameImplicits {
  implicit def autoWrapDataFrame(df: DataFrame): SciDataFrame =
    new SciDataFrame(df)
}
