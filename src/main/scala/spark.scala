/**
  * Created by bluejoe on 2018/5/6.
  */
package cn.piflow

import java.util.concurrent.atomic.AtomicInteger
import java.util.{Map => JMap}
import javax.script.{Compilable, ScriptEngineManager}

import cn.piflow.util.Logging
import org.apache.spark.sql._
import org.apache.spark.sql.catalyst.encoders.RowEncoder
import org.apache.spark.sql.types.StructType

import scala.collection.JavaConversions._
import scala.collection.immutable.StringOps
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

class SparkETLProcess extends Process with Logging {
  val ends = ArrayBuffer[(ProcessContext) => Unit]();
  val idgen = new AtomicInteger();

  override def run(pc: ProcessContext): Unit = {
    ends.foreach(_.apply(pc));
  }

  abstract class AbstractStream extends Stream {
    val id = idgen.incrementAndGet();
    val context = MMap[String, Any]();

    override def getId(): Int = id;

    def put(key: String, value: Any) = context(key) = value;

    override def get(key: String): Any = context.get(key);
  }

  def loadStream(streamSource: DataSource): Stream = {
    return new AbstractStream() {
      override def produce(ctx: ProcessContext): DataFrame = {
        logger.debug {
          val oid = this.getId();
          s"loading stream[_->$oid], source: $streamSource";
        };

        streamSource.load(ctx);
      }
    }
  }

  def writeStream(stream: Stream, streamSink: DataSink): Unit = {
    ends += {
      (ctx: ProcessContext) => {
        val input = stream.produce(ctx);
        logger.debug {
          val schema = input.schema;
          val iid = stream.getId();
          s"saving stream[$iid->_], schema: $schema, sink: $streamSink";
        };

        streamSink.save(input, ctx);
      }
    };
  }

  def transform(stream: Stream, transformer: DataTransformer): Stream = {
    return new AbstractStream() {
      override def produce(ctx: ProcessContext): DataFrame = {
        val input = stream.produce(ctx);
        logger.debug {
          val schema = input.schema;
          val iid = stream.getId();
          val oid = this.getId();
          s"transforming stream[$iid->$oid], schema: $schema, transformer: $transformer"
        };

        transformer.transform(input, ctx);
      }
    }
  }
}

trait Stream {
  def getId(): Int;

  def produce(ctx: ProcessContext): DataFrame;

  def get(key: String): Any;
}

trait DataSource {
  def load(ctx: ProcessContext): DataFrame;
}

trait DataTransformer {
  def transform(data: DataFrame, ctx: ProcessContext): DataFrame;
}

trait DataSink {
  def save(data: DataFrame, ctx: ProcessContext): Unit;
}

case class Console(nlimit: Int = 20) extends DataSink {
  override def save(data: DataFrame, ctx: ProcessContext): Unit = {
    data.show(nlimit);
  }
}

case class TextFile(path: String, format: String = FileFormat.TEXT) extends DataSource with DataSink {
  override def load(ctx: ProcessContext): DataFrame = {
    ctx.get[SparkSession].read.format(format).load(path).asInstanceOf[DataFrame];
  }

  override def save(data: DataFrame, ctx: ProcessContext): Unit = {
    data.write.format(format).save(path);
  }
}

object FileFormat {
  val TEXT = "text";
  val JSON = "json";
}

trait FunctionLogic {
  def call(value: Any): Any;
}

case class DoMap(func: FunctionLogic, targetSchema: StructType = null) extends DataTransformer {
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

case class DoFlatMap(func: FunctionLogic, targetSchema: StructType = null) extends DataTransformer {
  def transform(data: DataFrame, ctx: ProcessContext): DataFrame = {
    val encoder = RowEncoder {
      if (targetSchema == null) {
        data.schema;
      }
      else {
        targetSchema;
      }
    };

    data.flatMap(func.call(_).asInstanceOf[java.util.Iterator[Row]])(encoder);
  }
}

case class ExecuteSQL(sql: String) extends DataTransformer {
  def transform(data: DataFrame, ctx: ProcessContext): DataFrame = {

    try {
      data.createOrReplaceTempView("table0");
      ctx.get[SparkSession].sql(sql).asInstanceOf[DataFrame];
    }
    catch {
      case e: Throwable =>
        throw new SqlExecutionErrorException(e, sql);
    }
  }
}

class NoSuitableEncoderException(clazz: Class[_]) extends RuntimeException {
  override def getMessage: String = s"no suitable encoder for $clazz";
}

class SqlExecutionErrorException(cause: Throwable, sql: String)
  extends RuntimeException(s"sql execution error, sql: $sql", cause) {
}

class ScriptExecutionErrorException(cause: Throwable, sourceScript: String, args: Any)
  extends RuntimeException(s"script execution error, script: $sourceScript, args: $args", cause) {
}

class ScriptCompilationErrorException(cause: Throwable, sourceScript: String)
  extends RuntimeException(s"script execution error, script: $sourceScript", cause) {
}

trait ScriptEngine {
  def compile(funcText: String): CompiledFunction;
}


object ScriptEngine {
  val JAVASCRIPT = "javascript";
  val SCALA = "scala";
  val engines = Map[String, ScriptEngine](JAVASCRIPT -> new JavaScriptEngine());

  def get(lang: String) = engines(lang);

  def logic(script: String, lang: String = ScriptEngine.JAVASCRIPT): FunctionLogic = new FunctionLogic with Serializable {
    val cached = ArrayBuffer[CompiledFunction]();

    override def call(value: Any): Any = {
      if (cached.isEmpty) {
        try {
          val engine = ScriptEngine.get(lang);
          cached += engine.compile(script);
        }
        catch {
          case e: Throwable =>
            throw new ScriptExecutionErrorException(e, script, value);
        }
      }

      try {
        cached(0).invoke(Map("value" -> value));
      }
      catch {
        case e: Throwable =>
          throw new ScriptExecutionErrorException(e, script, value);
      };
    }
  }
}

trait CompiledFunction {
  def invoke(args: Map[String, Any] = Map[String, Any]()): Any;
}

class JavaScriptEngine extends ScriptEngine {
  val engine = new ScriptEngineManager().getEngineByName("javascript");

  val tools = {
    val map = MMap[String, AnyRef]();
    map += "$" -> Predef;
    map.toMap;
  }

  def compile(funcText: String): CompiledFunction = {
    val wrapped = s"($funcText)(value)";
    new CompiledFunction() {
      val compiled = engine.asInstanceOf[Compilable].compile(wrapped);

      def invoke(args: Map[String, Any] = Map[String, Any]()): Any = {
        val bindings = engine.createBindings();
        bindings.asInstanceOf[JMap[String, Any]].putAll(tools);
        bindings.asInstanceOf[JMap[String, Any]].putAll(args);

        val value = compiled.eval(bindings);
        value;
      }
    }
  }
}

object Predef {
  def StringOps(s: String) = new StringOps(s);

  def Row(value1: Any) = _row(value1);

  def Row(value1: Any, value2: Any) = _row(value1, value2);

  def Row(value1: Any, value2: Any, value3: Any) = _row(value1, value2, value3);

  def Row(value1: Any, value2: Any, value3: Any, value4: Any) = _row(value1, value2, value3, value4);

  private def _row(values: Any*) = org.apache.spark.sql.Row(values: _*);

  def Array() = new java.util.ArrayList();
}