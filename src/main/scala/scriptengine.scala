package cn.piflow

import java.util.{Map => JMap}
import javax.script.{Compilable, ScriptEngineManager}

import scala.collection.JavaConversions._
import scala.collection.immutable.StringOps
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

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
            throw new ScriptExecutionException(e, script, value);
        }
      }

      try {
        cached(0).invoke(Map("value" -> value));
      }
      catch {
        case e: Throwable =>
          throw new ScriptExecutionException(e, script, value);
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


class ScriptExecutionException(cause: Throwable, sourceScript: String, args: Any)
  extends RuntimeException(s"script execution error, script: $sourceScript, args: $args", cause) {
}

class ScriptCompilationException(cause: Throwable, sourceScript: String)
  extends RuntimeException(s"script compilation error, script: $sourceScript", cause) {
}

trait ScriptEngine {
  def compile(funcText: String): CompiledFunction;
}