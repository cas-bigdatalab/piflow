package cn.piflow

import java.util.concurrent.{CountDownLatch, TimeUnit}

import cn.piflow.util.{IdGenerator, Logging}
import org.apache.spark.sql._

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

trait ProcessInputStream {
  def isEmpty(): Boolean;

  def read(): DataFrame;

  def read(bundle: String): DataFrame;
}

trait ProcessOutputStream {
  def makeCheckPoint(pec: ProcessExecutionContext): Unit;

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

  def getFlowExecutionContext(): FlowExecutionContext;
}

trait Process {
  def initialize(ctx: FlowExecutionContext): Unit;

  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit;
}

trait Flow {
  def getProcessNames(): Seq[String];

  def hasCheckPoint(processName: String): Boolean;

  def getProcess(name: String): Process;

  def analyze(): AnalyzedFlowGraph;

  def show(): Unit;
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

case class Edge(processFrom: String, processTo: String, bundleOut: String, bundleIn: String) {
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

  def of(path: (Any, String)): Path = {
    val pi = new PathImpl();

    def _addEdges(path: (Any, String)): Unit = {
      val value1 = path._1;

      //String->String
      if (value1.isInstanceOf[String]) {
        pi.addEdge(new Edge(value1.asInstanceOf[String], path._2, "", ""));
      }

      //(String->String)->String
      else if (value1.isInstanceOf[(Any, String)]) {
        val tuple = value1.asInstanceOf[(Any, String)];
        _addEdges(tuple);
        pi.addEdge(new Edge(tuple._2, path._2, "", ""));
      }

      else {
        throw new InvalidPathException(value1);
      }
    }

    _addEdges(path);
    pi;
  }
}

class FlowImpl extends Flow {
  val edges = ArrayBuffer[Edge]();
  val processes = MMap[String, Process]();
  val checkpoints = ArrayBuffer[String]();

  def addProcess(name: String, process: Process) = {
    processes(name) = process;
    this;
  };

  override def show(): Unit = {
    edges.foreach { arrow =>
      println(arrow.toString());
    }
  }

  def addCheckPoint(processName: String): Unit = {
    checkpoints += processName;
  }

  override def hasCheckPoint(processName: String): Boolean = {
    checkpoints.contains(processName);
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

trait Runner {
  def bind(key: String, value: Any): Runner;

  def start(flow: Flow): FlowExecution;
}

object Runner {
  def create(): Runner = new Runner() {
    val ctx = new CascadeContext();

    override def bind(key: String, value: Any): this.type = {
      ctx.put(key, value);
      this;
    }

    override def start(flow: Flow): FlowExecution = {
      new FlowExecutionImpl(flow, ctx, this).start();
    }
  }
}

trait FlowExecution {
  def addListener(listener: FlowExecutionListener);

  def getExecutionId(): String;

  def awaitTermination();

  def awaitTermination(timeout: Long, unit: TimeUnit);

  def getFlow(): Flow;

  def fork(child: Flow): FlowExecution;

  def stop(): Unit;
}

trait FlowExecutionContext extends Context {
  def getFlow(): Flow;

  def getFlowExecution(): FlowExecution;
}

class ProcessInputStreamImpl() extends ProcessInputStream {
  //only returns DataFrame on calling read()
  val inputs = MMap[String, () => DataFrame]();

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
    inputs(bundle)();
  }
}

class ProcessOutputStreamImpl() extends ProcessOutputStream with Logging {
  override def makeCheckPoint(pec: ProcessExecutionContext) {
    mapDataFrame.foreach(en => {
      val path = pec.get("checkpoint.path").asInstanceOf[String].stripSuffix("/") + "/" + pec.getFlowExecutionContext().getFlowExecution().getExecutionId() + "/" + pec.getProcessExecution().getExecutionId();
      logger.debug(s"writing data on checkpoint: $path");
      en._2.apply().write.parquet(path);
      mapDataFrame(en._1) = () => {
        logger.debug(s"loading data from checkpoint: $path");
        pec.get[SparkSession].read.parquet(path)
      };
    })
  }

  val mapDataFrame = MMap[String, () => DataFrame]();

  override def write(data: DataFrame): Unit = write("", data);

  override def sendError(): Unit = ???

  override def write(bundle: String, data: DataFrame): Unit = {
    mapDataFrame(bundle) = () => data;
  }

  def contains(bundle: String) = mapDataFrame.contains(bundle);

  def getDataFrame(bundle: String) = mapDataFrame(bundle);
}

class FlowExecutionImpl(flow: Flow, runnerContext: Context, runner: Runner, parentExecution: Option[FlowExecution] = None)
  extends FlowExecution with Logging {

  val id = "flow_excution_" + IdGenerator.uuid() + "_" + IdGenerator.nextId[FlowExecution];
  val executionString = "" + id + parentExecution.map("(parent=" + _.toString + ")").getOrElse("");

  logger.debug(s"create execution: $this, flow: $flow");
  flow.show();

  val listeners = ArrayBuffer[FlowExecutionListener](new FlowExecutionLogger());
  val execution = this;
  val flowExecutionContext = createContext(runnerContext);
  val latch = new CountDownLatch(1);
  var running = false;

  val workerThread = new Thread(new Runnable() {
    def perform() {
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

          //is a checkpoint?
          if (flow.hasCheckPoint(processName)) {
            //store dataset
            outputs.makeCheckPoint(pe.getContext());
          }
        }
        catch {
          case e: Throwable =>
            listeners.foreach(_.onProcessFailed(pe.getContext()));
            throw e;
        }

        outputs;
      }
      );
    }

    override def run(): Unit = {
      running = true;

      //onFlowStarted
      listeners.foreach(_.onFlowStarted(flowExecutionContext));
      try {
        perform();
        //onFlowCompleted
        listeners.foreach(_.onFlowCompleted(flowExecutionContext));
      }
      //onFlowFailed
      catch {
        case e: Throwable =>
          listeners.foreach(_.onFlowFailed(flowExecutionContext));
          throw e;
      }
      finally {
        latch.countDown();
        running = false;
      }
    }
  });

  override def addListener(listener: FlowExecutionListener): Unit =
    listeners += listener;

  override def toString(): String = executionString;

  def start(): FlowExecutionImpl = {
    workerThread.start();
    this;
  }

  override def awaitTermination(): Unit = {
    latch.await();
  }

  override def awaitTermination(timeout: Long, unit: TimeUnit): Unit = {
    latch.await(timeout, unit);
    if (running)
      stop();
  }

  override def getExecutionId(): String = id;

  override def getFlow(): Flow = flow;

  private def createContext(runnerContext: Context): FlowExecutionContext = {
    new CascadeContext(runnerContext) with FlowExecutionContext {
      override def getFlow(): Flow = flow;

      override def getFlowExecution(): FlowExecution = execution;
    };
  }

  override def fork(child: Flow): FlowExecution = {
    //add flow execution stack
    val execution = new FlowExecutionImpl(child, runnerContext, runner, Some(this));
    execution.start();
    listeners.foreach(_.onFlowForked(flowExecutionContext, execution.flowExecutionContext));
    execution;
  }

  //TODO: stopSparkJob()
  override def stop(): Unit = {
    if (!running)
      throw new FlowNotRunningException(this);

    workerThread.interrupt();
    listeners.foreach(_.onFlowAborted(flowExecutionContext));
    latch.countDown();
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

  override def getFlowExecutionContext(): FlowExecutionContext = flowExecutionContext;
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

  def get(key: String, defaultValue: Any): Any;

  def get[T]()(implicit m: Manifest[T]): T = {
    get(m.runtimeClass.getName).asInstanceOf[T];
  }

  def put(key: String, value: Any): this.type;

  def put[T](value: T)(implicit m: Manifest[T]): this.type =
    put(m.runtimeClass.getName, value);
}

class CascadeContext(parent: Context = null) extends Context with Logging {
  val map = MMap[String, Any]();

  override def get(key: String): Any = internalGet(key,
    () => throw new ParameterNotSetException(key));

  override def get(key: String, defaultValue: Any): Any = internalGet(key,
    () => {
      logger.warn(s"value of '$key' not set, using default: $defaultValue");
      defaultValue;
    });

  def internalGet(key: String, op: () => Unit): Any = {
    if (map.contains(key)) {
      map(key);
    }
    else {
      if (parent != null)
        parent.get(key);
      else
        op();
    }
  };

  override def put(key: String, value: Any): this.type = {
    map(key) = value;
    this;
  }
}

trait FlowExecutionListener {
  def onFlowStarted(ctx: FlowExecutionContext);

  def onFlowForked(ctx: FlowExecutionContext, child: FlowExecutionContext);

  def onFlowCompleted(ctx: FlowExecutionContext);

  def onFlowFailed(ctx: FlowExecutionContext);

  def onFlowAborted(ctx: FlowExecutionContext);

  def onProcessInitialized(ctx: ProcessExecutionContext);

  def onProcessStarted(ctx: ProcessExecutionContext);

  def onProcessCompleted(ctx: ProcessExecutionContext);

  def onProcessFailed(ctx: ProcessExecutionContext);
}

class FlowExecutionLogger extends FlowExecutionListener with Logging {
  override def onFlowStarted(ctx: FlowExecutionContext): Unit = {
    val executionId = ctx.getFlowExecution().getExecutionId();
    logger.debug(s"flow started: $executionId");
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

  override def onFlowCompleted(ctx: FlowExecutionContext): Unit = {
    val executionId = ctx.getFlowExecution().getExecutionId();
    logger.debug(s"flow completed: $executionId");
  };

  override def onProcessCompleted(ctx: ProcessExecutionContext): Unit = {
    val processName = ctx.getProcessExecution().getProcessName();
    logger.debug(s"process completed: $processName");
  };

  override def onFlowFailed(ctx: FlowExecutionContext): Unit = {
    val executionId = ctx.getFlowExecution().getExecutionId();
    logger.debug(s"flow failed: $executionId");
  }

  override def onFlowAborted(ctx: FlowExecutionContext): Unit = {
    val executionId = ctx.getFlowExecution().getExecutionId();
    logger.debug(s"flow aborted: $executionId");
  }

  override def onFlowForked(ctx: FlowExecutionContext, child: FlowExecutionContext): Unit = {
    val executionId = ctx.getFlowExecution().getExecutionId();
    val childExecutionId = child.getFlowExecution().getExecutionId();
    logger.debug(s"flow forked: $executionId, child flow execution: $childExecutionId");
  }
}

class FlowException(msg: String = null, cause: Throwable = null) extends RuntimeException(msg, cause) {

}

class NoInputAvailableException extends FlowException() {

}

class ParameterNotSetException(key: String) extends FlowException(s"parameter not set: $key") {

}

//sub flow
class FlowAsProcess(flow: Flow) extends Process {
  override def initialize(ctx: FlowExecutionContext): Unit = {
  }

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    pec.getFlowExecutionContext().getFlowExecution().fork(flow).awaitTermination();
  }
}

class FlowNotRunningException(execution: FlowExecution) extends FlowException() {

}

class InvalidPathException(head: Any) extends FlowException() {

}