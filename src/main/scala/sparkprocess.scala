/**
  * Created by bluejoe on 2018/5/6.
  */
package cn.piflow

import cn.piflow.util.{IdGenerator, Logging}
import org.apache.spark.sql._
import org.apache.spark.sql.catalyst.encoders.RowEncoder
import org.apache.spark.sql.types.StructType

import scala.collection.JavaConversions
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

class SparkProcess extends Process with Logging {
  val ends = ArrayBuffer[(ProcessExecutionContext) => Unit]();

  def onPrepare(pec: ProcessExecutionContext) = {
    ends.foreach(_.apply(pec));
  }

  override def onCommit(pec: ProcessExecutionContext): Unit = {

  }

  override def onRollback(pec: ProcessExecutionContext): Unit = {

  }

  override def onFail(errorStage: ProcessStage, cause: Throwable, pec: ProcessExecutionContext): Unit = {

  }

  abstract class CachedStream extends Stream {
    val id = "" + IdGenerator.getNextId[Stream];
    val context = MMap[String, Any]();
    var cache: Option[DataFrame] = None;

    override def getId(): String = id;

    def put(key: String, value: Any) = context(key) = value;

    override def get(key: String): Any = context.get(key);

    def produce(ctx: ProcessExecutionContext): DataFrame;

    override def feed(ctx: ProcessExecutionContext): DataFrame = {
      if (!cache.isDefined) {
        cache = Some(produce(ctx));
      }
      cache.get;
    }
  }

  def loadStream(streamSource: DataSource): Stream = {
    return new CachedStream() {
      override def produce(ctx: ProcessExecutionContext): DataFrame = {
        logger.debug {
          val oid = this.getId();
          s"loading stream[_->$oid], source: $streamSource";
        };

        streamSource.load(ctx);
      }
    }
  }

  def writeStream(streamSink: DataSink, stream: Stream): Unit = {
    ends += {
      (ctx: ProcessExecutionContext) => {
        val input = stream.feed(ctx);
        logger.debug {
          val schema = input.schema;
          val iid = stream.getId();
          s"saving stream[$iid->_], schema: $schema, sink: $streamSink";
        };

        streamSink.save(input, ctx);
      }
    };
  }

  def transform(transformer: DataTransformer, streams: Stream*): Stream = {
    transform(transformer, streams.zipWithIndex.map(x => ("" + x._2, x._1)).toMap);
  }

  def transform(transformer: DataTransformer, streams: Map[String, Stream]): Stream = {
    return new CachedStream() {
      override def produce(ctx: ProcessExecutionContext): DataFrame = {
        val inputs = streams.map(x => (x._1, x._2.feed(ctx)));
        logger.debug {
          val schemas = inputs.map(_._2.schema);
          val iids = streams.map(_._2.getId());
          val oid = this.getId();
          s"transforming stream[$iids->$oid], schema: $schemas, transformer: $transformer"
        };

        transformer.transform(inputs, ctx);
      }
    }
  }
}

trait Stream {
  def getId(): String;

  def feed(ctx: ProcessExecutionContext): DataFrame;

  def get(key: String): Any;
}


trait DataSource {
  def load(ctx: ProcessExecutionContext): DataFrame;
}

trait DataTransformer {
  def transform(data: Map[String, DataFrame], ctx: ProcessExecutionContext): DataFrame;
}

trait DataTransformer1N1 extends DataTransformer {
  def transform(data: DataFrame, ctx: ProcessExecutionContext): DataFrame;

  def transform(dataset: Map[String, DataFrame], ctx: ProcessExecutionContext): DataFrame = {
    val first = dataset.head;
    transform(first._2, ctx);
  }
}

trait DataSink {
  def save(data: DataFrame, ctx: ProcessExecutionContext): Unit;
}

trait FunctionLogic {
  def call(value: Any): Any;
}

case class DoMap(func: FunctionLogic, targetSchema: StructType = null) extends DataTransformer1N1 {
  def transform(data: DataFrame, ctx: ProcessExecutionContext): DataFrame = {
    val encoder = RowEncoder {
      if (targetSchema == null) {
        data.schema;
      }
      else {
        targetSchema;
      }
    };

    data.map(func.call(_).asInstanceOf[Row])(encoder);
  }
}

case class DoFlatMap(func: FunctionLogic, targetSchema: StructType = null) extends DataTransformer1N1 {
  def transform(data: DataFrame, ctx: ProcessExecutionContext): DataFrame = {
    val encoder = RowEncoder {
      if (targetSchema == null) {
        data.schema;
      }
      else {
        targetSchema;
      }
    };

    data.flatMap(x =>
      JavaConversions.iterableAsScalaIterable(func.call(x).asInstanceOf[java.util.ArrayList[Row]]))(encoder);
  }
}

case class ExecuteSQL(sql: String) extends DataTransformer with Logging {
  def transform(dataset: Map[String, DataFrame], ctx: ProcessExecutionContext): DataFrame = {

    dataset.foreach { x =>
      val tableName = "table_" + x._1;
      logger.debug(s"registering sql table: $tableName");

      x._2.createOrReplaceTempView(tableName);
    }

    try {
      ctx.get[SparkSession].sql(sql);
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