package cn.piflow.lib.io

import java.io.File

import cn.piflow.JobContext
import cn.piflow.util.SciDataFrame
import cn.piflow.lib._
import cn.piflow.util.Logging
import org.apache.spark.sql._

/**
  * Created by bluejoe on 2018/5/13.
  */
case class TextFile(path: String, format: String = FileFormat.TEXT) extends Source with Sink {
    override def load(ctx: JobContext): SciDataFrame = {
      val sparkDf=ctx.get[SparkSession].read.format(format).load(path).asInstanceOf[DataFrame];
      new SciDataFrame(sparkDf)
    }

  override def save(data: SciDataFrame, ctx: JobContext): Unit = {
    data.save(path, format)
  }
}

object FileFormat {
  val TEXT = "text";
  val JSON = "json";
  val PARQUET = "parquet";
}

case class Console(nlimit: Int = 20) extends Sink {
  override def save(data: SciDataFrame, ctx: JobContext): Unit = {
    data.show(nlimit);
  }
}