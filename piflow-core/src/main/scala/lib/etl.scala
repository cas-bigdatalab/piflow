/**
  * Created by bluejoe on 2018/5/6.
  */
package cn.piflow.lib

import cn.piflow._
import cn.piflow.util.{FunctionLogic, Logging}
import org.apache.spark.sql._
import org.apache.spark.sql.catalyst.encoders.RowEncoder
import org.apache.spark.sql.types.StructType

import scala.collection.JavaConversions

class LoadStream(streamSource: Source) extends Process with Logging {
  override def initialize(ctx: FlowExecutionContext): Unit = {
  }

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    out.write(streamSource.load(pec));
  }
}

class WriteStream(streamSink: Sink) extends Process with Logging {
  override def initialize(ctx: FlowExecutionContext): Unit = {
  }

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    streamSink.save(in.read(), pec);
  }
}

trait Source {
  def load(ctx: ProcessExecutionContext): DataFrame;
}

trait Sink {
  def save(data: DataFrame, ctx: ProcessExecutionContext): Unit;
}

class DoMap(func: FunctionLogic, targetSchema: StructType = null) extends Process with Logging with Serializable {
  override def initialize(ctx: FlowExecutionContext): Unit = {
  }

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val input = in.read();
    val encoder = RowEncoder {
      if (targetSchema == null) {
        input.schema;
      }
      else {
        targetSchema;
      }
    };

    val output = input.map(x => func.perform(Seq(x)).asInstanceOf[Row])(encoder);
    out.write(output);
  }
}

class DoFlatMap(func: FunctionLogic, targetSchema: StructType = null) extends Process with Logging with Serializable {
  override def initialize(ctx: FlowExecutionContext): Unit = {

  }

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val data = in.read();
    val encoder = RowEncoder {
      if (targetSchema == null) {
        data.schema;
      }
      else {
        targetSchema;
      }
    };

    val output = data.flatMap(x =>
      JavaConversions.iterableAsScalaIterable(func.perform(Seq(x)).asInstanceOf[java.util.ArrayList[Row]]))(encoder);
    out.write(output);
  }
}

class ExecuteSQL(sql: String, bundle2TableName: (String, String)*) extends Process with Logging {
  override def initialize(ctx: FlowExecutionContext): Unit = {

  }

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    bundle2TableName.foreach { x =>
      val tableName = x._2;
      logger.debug(s"registering sql table: $tableName");

      in.read(x._1).createOrReplaceTempView(tableName);
    }

    try {
      val output = pec.get[SparkSession].sql(sql);
      out.write(output);
    }
    catch {
      case e: Throwable =>
        throw new SqlExecutionErrorException(sql, e);
    }
  }
}

class SqlExecutionErrorException(sql: String, cause: Throwable)
  extends RuntimeException(s"sql execution error, sql: $sql", cause) {
}