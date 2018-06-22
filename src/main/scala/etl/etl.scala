/**
  * Created by bluejoe on 2018/5/6.
  */
package cn.piflow.spark

import cn.piflow._
import cn.piflow.util.{IdGenerator, Logging}
import org.apache.spark.sql._
import org.apache.spark.sql.catalyst.encoders.RowEncoder
import org.apache.spark.sql.types.StructType

import scala.collection.JavaConversions
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

class ETLProcess extends Process with Logging {

  val ends = ArrayBuffer[Ops]();

  def loadStream(streamSource: Source): Stream = {
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

  def writeStream(streamSink: Sink, stream: Stream): Unit = {
    ends += SaveOps(streamSink, stream);
  }

  def transform(transformer: Transformer, streams: Stream*): Stream = {
    transform(transformer, streams.zipWithIndex.map(x => ("" + x._2, x._1)).toMap);
  }

  def transform(transformer: Transformer, streams: Map[String, Stream]): Stream = {
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

  trait Ops {
    def perform(ctx: ProcessExecutionContext): Unit;
  }

  abstract class CachedStream extends Stream {
    val id = "" + IdGenerator.nextId[Stream];
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

  case class SaveOps(streamSink: Sink, stream: Stream)
    extends Ops {
    def perform(ctx: ProcessExecutionContext): Unit = {
      val input = stream.feed(ctx);
      logger.debug {
        val schema = input.schema;
        val iid = stream.getId();
        s"saving stream[$iid->_], schema: $schema, sink: $streamSink";
      };

      streamSink.save(input, ctx);
    }
  }

  override def initialize(ctx: FlowExecutionContext): Unit = {

  }

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    ends.foreach(_.perform(pec));
  }

}

trait Stream {
  def getId(): String;

  def feed(ctx: ProcessExecutionContext): DataFrame;

  def get(key: String): Any;
}


trait Source {
  def load(ctx: ProcessExecutionContext): DataFrame;
}

trait Transformer {
  def transform(data: Map[String, DataFrame], ctx: ProcessExecutionContext): DataFrame;
}

trait Transformer1N1 extends Transformer {
  def transform(data: DataFrame, ctx: ProcessExecutionContext): DataFrame;

  def transform(dataset: Map[String, DataFrame], ctx: ProcessExecutionContext): DataFrame = {
    val first = dataset.head;
    transform(first._2, ctx);
  }
}

trait Sink {
  def save(data: DataFrame, ctx: ProcessExecutionContext): Unit;
}

trait FunctionLogic {
  def perform(value: Any): Any;
}

case class DoMap(func: FunctionLogic, targetSchema: StructType = null) extends Transformer1N1 {
  def transform(data: DataFrame, ctx: ProcessExecutionContext): DataFrame = {
    val encoder = RowEncoder {
      if (targetSchema == null) {
        data.schema;
      }
      else {
        targetSchema;
      }
    };

    data.map(func.perform(_).asInstanceOf[Row])(encoder);
  }
}

case class DoFlatMap(func: FunctionLogic, targetSchema: StructType = null) extends Transformer1N1 {
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
      JavaConversions.iterableAsScalaIterable(func.perform(x).asInstanceOf[java.util.ArrayList[Row]]))(encoder);
  }
}

case class ExecuteSQL(sql: String) extends Transformer with Logging {
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