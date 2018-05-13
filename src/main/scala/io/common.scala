package cn.piflow.io

import cn.piflow.{DataSink, ProcessExecutionContext, _}
import org.apache.spark.sql._

case class Console(nlimit: Int = 20) extends DataSink {
  override def save(data: DataFrame, ctx: ProcessExecutionContext): Unit = {
    data.show(nlimit);
  }
}

case class TextFile(path: String, format: String = FileFormat.TEXT) extends DataSource with DataSink {
  override def load(ctx: ProcessExecutionContext): DataFrame = {
    ctx.get[SparkSession].read.format(format).load(path).asInstanceOf[DataFrame];
  }

  override def save(data: DataFrame, ctx: ProcessExecutionContext): Unit = {
    data.write.format(format).save(path);
  }
}

object FileFormat {
  val TEXT = "text";
  val JSON = "json";
}