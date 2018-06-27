package cn.piflow.lib.io

import java.io.File

import cn.piflow.JobContext
import cn.piflow.lib._
import cn.piflow.util.Logging
import org.apache.spark.sql._

/**
  * Created by bluejoe on 2018/5/13.
  */
case class TextFile(path: String, format: String = FileFormat.TEXT) extends Source with Sink {
  override def load(ctx: JobContext): DataFrame = {
    ctx.get[SparkSession].read.format(format).load(path).asInstanceOf[DataFrame];
  }

  override def save(data: DataFrame, ctx: JobContext): Unit = {
    data.write.format(format).save(path);
  }
}

object FileFormat {
  val TEXT = "text";
  val JSON = "json";
  val PARQUET = "parquet";
}

case class Console(nlimit: Int = 20) extends Sink {
  override def save(data: DataFrame, ctx: JobContext): Unit = {
    data.show(nlimit);
  }
}