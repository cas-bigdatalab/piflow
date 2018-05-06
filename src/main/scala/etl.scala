/**
  * Created by bluejoe on 2018/5/6.
  */
package cn.piflow

import java.util.concurrent.atomic.AtomicInteger

import org.apache.spark.sql.DataFrame
import org.apache.spark.sql.execution.datasources.{FileFormat => SparkFileFormat}

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

class SparkETLProcess extends Process {
  val ends = ArrayBuffer[() => Unit]();
  val idgen = new AtomicInteger();

  override def run(pc: ProcessContext): Unit = {
    ends.foreach(_.apply());
  }

  abstract class AbstractStream extends Stream {
    val id = idgen.incrementAndGet();

    override def getId(): Int = id;
  }

  def loadStream(streamSource: StreamSource): Stream = {
    return new AbstractStream() {
      override def getDataFrame(): DataFrame = {
        println("load");
        null;
      }
    }
  }

  def writeStream(stream: Stream, streamSink: StreamSink): Unit = {
    ends += { () => {
      println("write");
      stream.getDataFrame().show();
    }
    };
  }

  def transform(stream: Stream, transformer: Transformer): Stream = {
    return new AbstractStream() {
      override def getDataFrame(): DataFrame = {
        println("transform");
        stream.getDataFrame();
      }
    }
  }
}

trait Stream {
  def getId(): Int;

  def getDataFrame(): DataFrame;
}

trait StreamSource {

}

trait Transformer {

}

trait StreamSink {

}

case class TextFile(path: String, format: String) extends StreamSource with StreamSink {

}

case class DoMap(mapFunc: String) extends Transformer {

}

case class DoFlatMap(mapFunc: String) extends Transformer {

}