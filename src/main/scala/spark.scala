/**
  * Created by bluejoe on 2018/5/6.
  */
package cn.piflow

import java.util.concurrent.atomic.AtomicInteger
import java.util.{Map => JMap}
import javax.script.{Compilable, CompiledScript => JCompiledScript, ScriptEngineManager}

import org.apache.spark.api.java.function.{FlatMapFunction, MapFunction}
import org.apache.spark.sql.{Dataset, Encoder, Encoders, SparkSession}

import scala.collection.JavaConversions._
import scala.collection.immutable.StringOps
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

class SparkETLProcess extends Process {
  val ends = ArrayBuffer[(SparkProcessContext) => Unit]();
  val idgen = new AtomicInteger();

  override def run(pc: ProcessContext): Unit = {
    ends.foreach(_.apply(pc.asInstanceOf[SparkProcessContext]));
  }

  abstract class AbstractStream extends Stream {
    val id = idgen.incrementAndGet();
    val context = MMap[String, Any]();

    override def getId(): Int = id;

    def put(key: String, value: Any) = context(key) = value;

    override def get(key: String): Any = context.get(key);
  }

  def loadStream(streamSource: DatasetSource): Stream = {
    return new AbstractStream() {
      override def singleDataset(ctx: SparkProcessContext): Dataset[Any] = {
        streamSource.loadDataset(ctx);
      }
    }
  }

  def writeStream(stream: Stream, streamSink: DatasetSink): Unit = {
    ends += { (ctx: SparkProcessContext) => {
      streamSink.saveDataset(stream.singleDataset(ctx), ctx);
    }
    };
  }

  def transform(stream: Stream, transformer: DatasetTransformer): Stream = {
    return new AbstractStream() {
      override def singleDataset(ctx: SparkProcessContext): Dataset[Any] = {
        transformer.transform(stream.singleDataset(ctx), ctx);
      }
    }
  }
}

class SparkProcessContext extends ProcessContext {
  val spark = SparkSession.builder.master("local[4]")
    .getOrCreate();
  super.put(classOf[SparkSession].getName, spark);

  def getSparkSession() = get(classOf[SparkSession].getName).asInstanceOf[SparkSession];
}

trait Stream {
  def getId(): Int;

  def singleDataset(ctx: SparkProcessContext): Dataset[Any];

  def get(key: String): Any;
}

trait DatasetSource {
  def loadDataset(ctx: SparkProcessContext): Dataset[Any];
}

trait DatasetTransformer {
  def transform(dataset: Dataset[Any], ctx: SparkProcessContext): Dataset[Any];
}

trait DatasetSink {
  def saveDataset(dataset: Dataset[Any], ctx: SparkProcessContext): Unit;
}

case class TextFile(path: String, format: String) extends DatasetSource with DatasetSink {
  override def loadDataset(ctx: SparkProcessContext): Dataset[Any] = {
    ctx.getSparkSession().read.textFile(path).asInstanceOf[Dataset[Any]];
  }

  override def saveDataset(dataset: Dataset[Any], ctx: SparkProcessContext): Unit = {
    dataset.write.json(path);
  }
}

case class DoMap(mapFuncText: String, targetClass: Class[_], lang: String = ScriptEngine.JAVASCRIPT) extends DatasetTransformer {
  def transform(dataset: Dataset[Any], ctx: SparkProcessContext): Dataset[Any] = {
    dataset.map(new MapFunction[Any, Any]() {
      val cached = ArrayBuffer[CompiledFunction]();

      override def call(value: Any): Any = {
        if (cached.isEmpty) {
          try {
            val engine = ScriptEngine.get(lang);
            cached += engine.compile(mapFuncText);
          }
          catch {
            case e: Throwable =>
              throw new ScriptExecutionErrorException(e, mapFuncText, value);
          }
        }

        try {
          cached(0).invoke(Map("value" -> value));
        }
        catch {
          case e: Throwable =>
            throw new ScriptExecutionErrorException(e, mapFuncText, value);
        };
      }
    }, EncoderManager.encoderFor(targetClass));
  }
}

case class DoFlatMap(mapFuncText: String, targetClass: Class[_], lang: String = ScriptEngine.JAVASCRIPT) extends DatasetTransformer {
  def transform(dataset: Dataset[Any], ctx: SparkProcessContext): Dataset[Any] = {
    dataset.flatMap(new FlatMapFunction[Any, Any]() {
      val cached = ArrayBuffer[CompiledFunction]();

      override def call(value: Any): java.util.Iterator[Any] = {
        if (cached.isEmpty) {
          try {
            val engine = ScriptEngine.get(lang);
            cached += engine.compile(mapFuncText);
          }
          catch {
            case e: Throwable =>
              throw new ScriptCompilationErrorException(e, mapFuncText);
          }
        }

        try {
          cached(0).invoke(Map("value" -> value))
            .asInstanceOf[java.util.Collection[_]]
            .iterator
            .asInstanceOf[java.util.Iterator[Any]];
        }
        catch {
          case e: Throwable =>
            throw new ScriptExecutionErrorException(e, mapFuncText, value);
        };
      }
    }, EncoderManager.encoderFor(targetClass));
  }
}

object EncoderManager {
  val stockEncoders = Map[Class[_], Encoder[_]](
    classOf[java.lang.String] -> Encoders.STRING,
    classOf[java.lang.Integer] -> Encoders.INT,
    classOf[java.lang.Boolean] -> Encoders.BOOLEAN,
    classOf[java.lang.Float] -> Encoders.FLOAT,
    classOf[java.lang.Double] -> Encoders.DOUBLE,
    classOf[Int] -> Encoders.scalaInt
  );

  def encoderFor(clazz: Class[_]): Encoder[Any] = {
    if (stockEncoders.contains(clazz))
      stockEncoders(clazz).asInstanceOf[Encoder[Any]];
    else
      throw new NoSuitableEncoderException(clazz);
  }
}

class NoSuitableEncoderException(clazz: Class[_]) extends RuntimeException {
  override def getMessage: String = s"no suitable encoder for $clazz";
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
}

trait CompiledFunction {
  def invoke(args: Map[String, Any] = Map[String, Any]()): Any;
}

class JavaScriptEngine extends ScriptEngine {
  val engine = new ScriptEngineManager().getEngineByName("javascript");
  engine.put("Tool", Tool);

  def compile(funcText: String): CompiledFunction = {
    val wrapped = s"($funcText)(value)";
    new CompiledFunction() {
      val compiled = engine.asInstanceOf[Compilable].compile(wrapped);

      def invoke(args: Map[String, Any] = Map[String, Any]()): Any = {
        val bindings = engine.createBindings();
        bindings.asInstanceOf[JMap[String, Any]].putAll(args);

        val value = compiled.eval(bindings);
        value;
      }
    }
  }
}

object Tool {
  def ops(s: String) = new StringOps(s);
}