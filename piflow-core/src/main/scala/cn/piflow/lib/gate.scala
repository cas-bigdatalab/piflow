package cn.piflow.lib

import cn.piflow._
import cn.piflow.util.SciDataFrame

class DoMerge extends Stop {
  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    out.write(new SciDataFrame(in.ports().map(in.read(_).getSparkDf).reduce((x, y) => x.union(y))));
  }
}

class DoFork(outports: Seq[String] = Seq("op1", "op2")) extends Stop {
  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    outports.foreach(out.write(_, in.read()));
  }
}
