package cn.piflow.spark.io

import java.io.File

import cn.piflow.ProcessExecutionContext
import cn.piflow.spark._
import cn.piflow.util.Logging
import org.apache.spark.sql._

/**
  * Created by bluejoe on 2018/5/13.
  */
case class TextFile(path: String, format: String = FileFormat.TEXT) extends Source with SinkWithBackup {
  override def load(ctx: ProcessExecutionContext): DataFrame = {
    ctx.get[SparkSession].read.format(format).load(path).asInstanceOf[DataFrame];
  }

  override def save(data: DataFrame, ctx: ProcessExecutionContext): Unit = {
    data.write.format(format).save(path);
  }

  def backup(ctx: ProcessExecutionContext): Backup = new Backup() with Logging {
    val backupFile = File.createTempFile(classOf[TextFile].getName.toLowerCase + "_", ".tmp",
      new File(ctx.get("localBackupDir").asInstanceOf[String]));
    backupFile.delete();

    override def getSink(): Sink = TextFile(backupFile.getAbsolutePath, format);

    override def commit(): Unit = {
      logger.debug {
        val src = backupFile.getAbsolutePath;
        s"rename $src to $path"
      };
      backupFile.renameTo(new File(path));
    };

    override def rollback(): Unit = {
      backupFile.delete();
    }
  }
}

object FileFormat {
  val TEXT = "text";
  val JSON = "json";
  val PARQUET = "parquet";
}

case class Console(nlimit: Int = 20) extends Sink {
  override def save(data: DataFrame, ctx: ProcessExecutionContext): Unit = {
    data.show(nlimit);
  }
}