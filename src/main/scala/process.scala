package cn.piflow

import cn.piflow.util.{IdGenerator, Logging}
import org.quartz._

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

trait Process {
  def onPrepare(pec: ProcessExecutionContext): Unit;

  def onCommit(pec: ProcessExecutionContext): Unit;

  def onRollback(pec: ProcessExecutionContext): Unit;

  def onFail(errorStage: ProcessStage, cause: Throwable, pec: ProcessExecutionContext): Unit;
}

abstract class LazyProcess extends Process with Logging {
  def onPrepare(pec: ProcessExecutionContext): Unit = {
    logger.warn(s"onPrepare={}, process: $this");
  }

  def onCommit(pec: ProcessExecutionContext): Unit;

  def onRollback(pec: ProcessExecutionContext): Unit = {
    logger.warn(s"onRollback={}, process: $this");
  }

  def onFail(errorStage: ProcessStage, cause: Throwable, pec: ProcessExecutionContext): Unit = {}
}

//TODO: one ProcessExecution with multiple RUNs
trait ProcessExecution {
  def getId(): String;

  def start();

  def getProcessName(): String;

  def getProcess(): Process;

  def getStage(): ProcessStage;

  def handleError(jee: JobExecutionException): Unit;
}

trait ProcessExecutionContext extends Context {
  def getProcessExecution(): ProcessExecution;

  def setStage(stage: ProcessStage): Unit;

  def getStage(): ProcessStage;

  def setErrorHandler(handler: ErrorHandler): Unit;
}

class ProcessExecutionContextImpl(processExecution: ProcessExecution, executionContext: FlowExecutionContext)
  extends ProcessExecutionContext {
  val stages = ArrayBuffer[ProcessStage]();
  var errorHandler: ErrorHandler = Noop();

  def setStage(stage: ProcessStage) = stages += stage;

  val context = MMap[String, Any]();

  def getProcessExecution() = processExecution;

  def getStage(): ProcessStage = stages.last;

  override def get(key: String): Any = {
    if (context.contains(key))
      context(key);
    else
      executionContext.get(key);
  };

  override def put(key: String, value: Any): this.type = {
    context(key) = value;
    this;
  };

  override def setErrorHandler(handler: ErrorHandler): Unit = errorHandler = handler;
}

class ProcessAsQuartzJob extends Job with Logging {
  override def execute(context: JobExecutionContext): Unit = {
    val map = context.getJobDetail.getJobDataMap;
    val processName = map.get("processName").asInstanceOf[String];
    val executionContext = context.getScheduler.getContext.get("executionContext").asInstanceOf[FlowExecutionContext];

    val pe = executionContext.runProcess(processName);
    try {
      pe.start();
      context.setResult(true);
    }
    catch {
      case e => {
        val jee = new JobExecutionException(s"failed to execute process: $processName", e);
        logger.error {
          val stage = pe.getStage();
          s"failed to execute process: $processName, stage: $stage, cause: $e"
        };
        pe.handleError(jee);
        throw jee;
      };
    }
  }
}

class ProcessExecutionImpl(processName: String, process: Process, executionContext: FlowExecutionContext)
  extends ProcessExecution with Logging {
  val id = "process_excution_" + IdGenerator.getNextId[ProcessExecution];
  val processExecutionContext = createContext();

  override def getId(): String = id;

  override def start(): Unit = {
    try {
      processExecutionContext.setStage(PrepareStart());
      process.onPrepare(processExecutionContext);
      processExecutionContext.setStage(PrepareComplete());
    }
    catch {
      case e =>
        try {
          logger.warn(s"onPrepare() failed: $e");
          processExecutionContext.setStage(RollbackStart());
          process.onRollback(processExecutionContext);
          processExecutionContext.setStage(RollbackComplete());

          throw e;
        }
        catch {
          case e =>
            logger.warn(s"onRollback() failed: $e");
            process.onFail(RollbackStart(), e, processExecutionContext);
            throw e;
        }
    }

    try {
      processExecutionContext.setStage(CommitStart());
      process.onCommit(processExecutionContext);
      processExecutionContext.setStage(CommitComplete());
    }
    catch {
      case e =>
        logger.warn(s"onCommit() failed: $e");
        process.onFail(CommitStart(), e, processExecutionContext);
        throw e;
    }
  }

  private def createContext() =
    new ProcessExecutionContextImpl(this, executionContext);

  override def getProcessName(): String = processName;

  override def getProcess(): Process = process;

  override def handleError(jee: JobExecutionException): Unit = processExecutionContext.errorHandler.handle(jee);

  override def getStage(): ProcessStage = processExecutionContext.getStage();
}

trait ErrorHandler {
  def handle(jee: JobExecutionException);
}

case class Noop() extends ErrorHandler {
  def handle(jee: JobExecutionException): Unit = {
  }
}

case class Retry() extends ErrorHandler {
  def handle(jee: JobExecutionException): Unit = {
    jee.setRefireImmediately(true);
  }
}

case class Abort() extends ErrorHandler {
  def handle(jee: JobExecutionException): Unit = {
    jee.setUnscheduleFiringTrigger(true);
  }
}

case class Fail() extends ErrorHandler {
  def handle(jee: JobExecutionException): Unit = {
    jee.setUnscheduleAllTriggers(true);
  }
}

trait ProcessStage {
  def getName(): String;
}

case class PrepareStart() extends ProcessStage {
  def getName(): String = this.getClass.getSimpleName;
}

case class PrepareComplete() extends ProcessStage {
  def getName(): String = this.getClass.getSimpleName;
}

case class CommitStart() extends ProcessStage {
  def getName(): String = this.getClass.getSimpleName;
}

case class CommitComplete() extends ProcessStage {
  def getName(): String = this.getClass.getSimpleName;
}

case class RollbackStart() extends ProcessStage {
  def getName(): String = this.getClass.getSimpleName;
}

case class RollbackComplete() extends ProcessStage {
  def getName(): String = this.getClass.getSimpleName;
}