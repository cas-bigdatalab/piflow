/**
  * Created by bluejoe on 2018/5/6.
  */
package cn.piflow

import java.util.concurrent.atomic.AtomicInteger

import cn.piflow.util.Logging
import org.apache.spark.sql._
import org.apache.spark.sql.catalyst.encoders.RowEncoder
import org.apache.spark.sql.types.StructType

import scala.collection.JavaConversions
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

class SparkETLProcess extends Process with Logging {
  val ends = ArrayBuffer[(ProcessContext) => Unit]();
  val idgen = new AtomicInteger();

  override def run(pc: ProcessContext): Unit = {
    ends.foreach(_.apply(pc));
  }

  abstract class CachedStream extends Stream {
    val id = idgen.incrementAndGet();
    val context = MMap[String, Any]();
    var cache: Option[DataFrame] = None;

    override def getId(): Int = id;

    def put(key: String, value: Any) = context(key) = value;

    override def get(key: String): Any = context.get(key);

    def produce(ctx: ProcessContext): DataFrame;

    override def feed(ctx: ProcessContext): DataFrame = {
      if (!cache.isDefined) {
        cache = Some(produce(ctx));
      }
      cache.get;
    }
  }

  def loadStream(streamSource: DataSource): Stream = {
    return new CachedStream() {
      override def produce(ctx: ProcessContext): DataFrame = {
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
      (ctx: ProcessContext) => {
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
      override def produce(ctx: ProcessContext): DataFrame = {
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
  def getId(): Int;

  def feed(ctx: ProcessContext): DataFrame;

  def get(key: String): Any;
}


trait DataSource {
  def load(ctx: ProcessContext): DataFrame;
}

trait DataTransformer {
  def transform(data: Map[String, DataFrame], ctx: ProcessContext): DataFrame;
}

trait DataTransformer1N1 extends DataTransformer {
  def transform(data: DataFrame, ctx: ProcessContext): DataFrame;

  def transform(dataset: Map[String, DataFrame], ctx: ProcessContext): DataFrame = {
    val first = dataset.head;
    transform(first._2, ctx);
  }
}

trait DataSink {
  def save(data: DataFrame, ctx: ProcessContext): Unit;
}

trait FunctionLogic {
  def call(value: Any): Any;
}

case class DoMap(func: FunctionLogic, targetSchema: StructType = null) extends DataTransformer1N1 {
  def transform(data: DataFrame, ctx: ProcessContext): DataFrame = {
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
  def transform(data: DataFrame, ctx: ProcessContext): DataFrame = {
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
  def transform(dataset: Map[String, DataFrame], ctx: ProcessContext): DataFrame = {

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
        throw new SqlExecutionErrorException(e, sql);
    }
  }
}

class SqlExecutionErrorException(cause: Throwable, sql: String)
  extends RuntimeException(s"sql execution error, sql: $sql", cause) {
}