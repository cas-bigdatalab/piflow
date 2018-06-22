package cn.piflow

import cn.piflow.util.{IdGenerator, Logging}
import org.apache.spark.sql._

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

trait ProcessInputStream {
  def isEmpty(): Boolean;

  def read(): DataFrame;

  def read(bundle: String): DataFrame;
}

trait ProcessOutputStream {
  def write(data: DataFrame);

  def write(bundle: String, data: DataFrame);

  def sendError();
}

trait ProcessExecution {
  def getExecutionId(): String;

  def getProcessName(): String;

  def getProcess(): Process;
}

trait ProcessExecutionContext extends Context {
  def getProcessExecution(): ProcessExecution;

  def getInputStream(): ProcessInputStream;

  def getOutputStream(): ProcessOutputStream;
}

trait Process {
  def initialize(ctx: FlowExecutionContext): Unit;

  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit;
}

trait Flow {
  def getProcessNames(): Seq[String];

  def getProcess(name: String): Process;

  def analyze(): AnalyzedFlowGraph;
}

trait Path {
  def toEdges(): Seq[Edge];

  def addEdge(edge: Edge): Path;

  def to(processTo: String, bundleOut: String = "", bundleIn: String = ""): Path;
}

class PathImpl() extends Path {
  val edges = ArrayBuffer[Edge]();

  override def toEdges(): Seq[Edge] = edges.toSeq;

  override def addEdge(edge: Edge): Path = {
    edges += edge;
    this;
  }

  override def to(processTo: String, bundleOut: String, bundleIn: String): Path = {
    edges += new Edge(edges.last.processTo, processTo, bundleOut, bundleIn);
    this;
  }
}

class Edge(val processFrom: String, var processTo: String, var bundleOut: String, var bundleIn: String) {
  override def toString() = {
    s"[$processFrom]-($bundleOut)-($bundleIn)-[$processTo]";
  }
}

object Path {

  trait PathHead {
    def to(processTo: String, bundleOut: String = "", bundleIn: String = ""): Path;
  }

  def from(processFrom: String): PathHead = {
    new PathHead() {
      override def to(processTo: String, bundleOut: String, bundleIn: String): Path = {
        val path = new PathImpl();
        path.addEdge(new Edge(processFrom, processTo, bundleOut, bundleIn));
        path;
      }
    };
  }
}

class FlowImpl extends Flow {
  val edges = ArrayBuffer[Edge]();
  val processes = MMap[String, Process]();

  def addProcess(name: String, process: Process) = {
    processes(name) = process;
    this;
  };

  def print(): Unit = {
    edges.foreach { arrow =>
      println(arrow.toString());
    }
  }

  override def getProcess(name: String) = processes(name);

  override def getProcessNames(): Seq[String] = processes.map(_._1).toSeq;

  def addPath(path: Path): Flow = {
    edges ++= path.toEdges();
    this;
  }

  override def analyze(): AnalyzedFlowGraph =
    new AnalyzedFlowGraph() {
      val incomingEdges = MMap[String, ArrayBuffer[Edge]]();
      val outgoingEdges = MMap[String, ArrayBuffer[Edge]]();

      edges.foreach { edge =>
        incomingEdges.getOrElseUpdate(edge.processTo, ArrayBuffer[Edge]()) += edge;
        outgoingEdges.getOrElseUpdate(edge.processFrom, ArrayBuffer[Edge]()) += edge;
      }

      private def _visitProcess[T](processName: String, op: (String, Map[Edge, T]) => T, visited: MMap[String, T]): T = {
        if (!visited.contains(processName)) {
          //executes dependent processes
          val inputs =
            if (incomingEdges.contains(processName)) {
              //all incoming edges
              val edges = incomingEdges(processName);
              edges.map { edge =>
                edge ->
                  _visitProcess(edge.processFrom, op, visited);
              }.toMap
            }
            else {
              Map[Edge, T]();
            }

          val ret = op(processName, inputs);
          visited(processName) = ret;
          ret;
        }
        else {
          visited(processName);
        }
      }

      override def visit[T](op: (String, Map[Edge, T]) => T): Unit = {
        val ends = processes.keys.filterNot(outgoingEdges.contains(_));
        val visited = MMap[String, T]();
        ends.foreach {
          _visitProcess(_, op, visited);
        }
      }
    }
}

trait AnalyzedFlowGraph {
  def visit[T](op: (String, Map[Edge, T]) => T): Unit;
}

object Runner {
  val ctx = new CascadeContext();

  def bind(key: String, value: Any): this.type = {
    ctx.put(key, value);
    this;
  }

  def run(flow: Flow): FlowExecution = {
    new FlowExecutionImpl(flow, ctx);
  }
}

trait FlowExecution {
  def addListener(listener: FlowExecutionListener);

  def getExecutionId(): String;

  def start();

  def getFlow(): Flow;
}

trait FlowExecutionContext extends Context {
  def getFlow(): Flow;

  def getFlowExecution(): FlowExecution;
}

class ProcessInputStreamImpl() extends ProcessInputStream {
  val inputs = MMap[String, DataFrame]();

  override def isEmpty(): Boolean = inputs.isEmpty;

  def attach(inputs: Map[Edge, ProcessOutputStreamImpl]) = {
    this.inputs ++= inputs.filter(x => x._2.contains(x._1.bundleOut))
      .map(x => (x._1.bundleIn, x._2.getDataFrame(x._1.bundleOut)));
  };

  override def read(): DataFrame = {
    if (inputs.isEmpty)
      throw new NoInputAvailableException();

    read(inputs.head._1);
  };

  override def read(bundle: String): DataFrame = {
    inputs(bundle);
  }
}

class ProcessOutputStreamImpl() extends ProcessOutputStream {
  val mapDataFrame = MMap[String, DataFrame]();

  override def write(data: DataFrame): Unit = write("", data);

  override def sendError(): Unit = ???

  override def write(bundle: String, data: DataFrame): Unit = {
    mapDataFrame(bundle) = data;
  }

  def contains(bundle: String) = mapDataFrame.contains(bundle);

  def getDataFrame(bundle: String) = mapDataFrame(bundle);
}

class FlowExecutionImpl(flow: Flow, runnerContext: Context)
  extends FlowExecution with Logging {

  val listeners = ArrayBuffer[FlowExecutionListener](new FlowExecutionLogger());

  val id = "flow_excution_" + IdGenerator.nextId[FlowExecution];
  val execution = this;
  val flowExecutionContext = createContext(runnerContext);

  override def addListener(listener: FlowExecutionListener): Unit =
    listeners += listener;

  override def start(): Unit = {

    listeners.foreach(_.onFlowStarted(flowExecutionContext));

    //initialize all processes
    //initialize process context
    val executions = MMap[String, ProcessExecutionImpl]();
    flow.getProcessNames().foreach { processName =>
      val process = flow.getProcess(processName);
      process.initialize(flowExecutionContext);

      val pe = new ProcessExecutionImpl(processName, process, flowExecutionContext);
      executions(processName) = pe;
      listeners.foreach(_.onProcessInitialized(pe.getContext()));
    }

    val analyzed = flow.analyze();

    //runs processes
    analyzed.visit[ProcessOutputStreamImpl]((processName: String, inputs: Map[Edge, ProcessOutputStreamImpl]) => {
      val pe = executions(processName);
      var outputs: ProcessOutputStreamImpl = null;
      try {
        outputs = pe.perform(inputs);
        listeners.foreach(_.onProcessCompleted(pe.getContext()));
      }
      catch {
        case e: Throwable =>
          listeners.foreach(_.onProcessFailed(pe.getContext()));
          throw e;
      }

      outputs;
    }
    );

    listeners.foreach(_.onFlowShutdown(flowExecutionContext));
  }

  override def getExecutionId(): String = id;

  override def getFlow(): Flow = flow;

  private def createContext(runnerContext: Context): FlowExecutionContext = {
    new CascadeContext(runnerContext) with FlowExecutionContext {
      override def getFlow(): Flow = flow;

      override def getFlowExecution(): FlowExecution = execution;
    };
  }
}

class ProcessExecutionContextImpl(processExecution: ProcessExecution, flowExecutionContext: FlowExecutionContext)
  extends CascadeContext(flowExecutionContext)
    with ProcessExecutionContext
    with Logging {
  val is: ProcessInputStreamImpl = new ProcessInputStreamImpl();

  val os = new ProcessOutputStreamImpl();

  def getProcessExecution() = processExecution;

  def getInputStream(): ProcessInputStream = is;

  def getOutputStream(): ProcessOutputStream = os;
}

class ProcessExecutionImpl(processName: String, process: Process, flowExecutionContext: FlowExecutionContext)
  extends ProcessExecution with Logging {
  val id = "process_excution_" + IdGenerator.nextId[ProcessExecution];
  val pec = new ProcessExecutionContextImpl(this, flowExecutionContext);

  override def getExecutionId(): String = id;

  def getContext() = pec;

  def perform(inputs: Map[Edge, ProcessOutputStreamImpl]): ProcessOutputStreamImpl = {
    pec.getInputStream().asInstanceOf[ProcessInputStreamImpl].attach(inputs);
    process.perform(pec.getInputStream(), pec.getOutputStream(), pec);
    pec.getOutputStream().asInstanceOf[ProcessOutputStreamImpl];
  }

  override def getProcessName(): String = processName;

  override def getProcess(): Process = process;
}

trait Context {
  def get(key: String): Any;

  def get[T]()(implicit m: Manifest[T]): T = {
    get(m.runtimeClass.getName).asInstanceOf[T];
  }

  def put(key: String, value: Any): this.type;

  def put[T](value: T)(implicit m: Manifest[T]): this.type =
    put(m.runtimeClass.getName, value);
}

class CascadeContext(parent: Context = null) extends Context {
  val map = MMap[String, Any]();

  override def get(key: String): Any = {
    if (map.contains(key)) {
      map(key);
    }
    else {
      if (parent != null)
        parent.get(key);
      else
        null;
    }
  };

  override def put(key: String, value: Any): this.type = {
    map(key) = value;
    this;
  }
}

trait FlowExecutionListener {
  def onFlowStarted(ctx: FlowExecutionContext);

  def onFlowShutdown(ctx: FlowExecutionContext);

  def onProcessInitialized(ctx: ProcessExecutionContext);

  def onProcessStarted(ctx: ProcessExecutionContext);

  def onProcessCompleted(ctx: ProcessExecutionContext);

  def onProcessFailed(ctx: ProcessExecutionContext);
}

class FlowExecutionLogger extends FlowExecutionListener with Logging {
  override def onFlowStarted(ctx: FlowExecutionContext): Unit = {
    val flowName = ctx.getFlow().toString;
    logger.debug(s"flow started: $flowName");
  };

  override def onProcessStarted(ctx: ProcessExecutionContext): Unit = {
    val processName = ctx.getProcessExecution().getProcessName();
    logger.debug(s"process started: $processName");
  };

  override def onProcessFailed(ctx: ProcessExecutionContext): Unit = {
    val processName = ctx.getProcessExecution().getProcessName();
    logger.debug(s"process failed: $processName");
  };

  override def onProcessInitialized(ctx: ProcessExecutionContext): Unit = {
    val processName = ctx.getProcessExecution().getProcessName();
    logger.debug(s"process initialized: $processName");
  };

  override def onFlowShutdown(ctx: FlowExecutionContext): Unit = {
    val flowName = ctx.getFlow().toString;
    logger.debug(s"flow shutdown: $flowName");
  };

  override def onProcessCompleted(ctx: ProcessExecutionContext): Unit = {
    val processName = ctx.getProcessExecution().getProcessName();
    logger.debug(s"process completed: $processName");
  };
}

class FlowException extends RuntimeException {

}

class NoInputAvailableException extends FlowException {

}