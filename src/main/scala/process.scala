package cn.piflow

import cn.piflow.util.{IdGenerator, Logging}
import org.quartz._

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

trait Process {
  def onPrepare(pec: ProcessExecutionContext): Unit;

  def onCommit(pec: ProcessExecutionContext): Unit;

  def onRollback(pec: ProcessExecutionContext): Unit;
}

abstract class LazyProcess extends Process with Logging {
  def onPrepare(pec: ProcessExecutionContext): Unit = {
    logger.warn(s"onPrepare={}, process: $this");
  }

  def onCommit(pec: ProcessExecutionContext): Unit;

  def onRollback(pec: ProcessExecutionContext): Unit = {
    logger.warn(s"onRollback={}, process: $this");
  }
}

//TODO: one ProcessExecution with multiple RUNs
trait ProcessExecution {
  def getId(): String;

  def start();

  def getProcessName(): String;

  def getProcess(): Process;
}

trait ProcessExecutionContext extends Context {
  def getProcessExecution(): ProcessExecution;

  def setStage(stage: ProcessStage): Unit;

  def sendError(stage: ProcessStage, cause: Throwable): Unit;

  def getStage(): ProcessStage;
}

class ProcessExecutionContextImpl(processExecution: ProcessExecution, executionContext: FlowExecutionContext)
  extends ProcessExecutionContext with Logging {
  val stages = ArrayBuffer[ProcessStage]();
  val context = MMap[String, Any]();
  var errorHandler: ErrorHandler = Noop();

  def getProcessExecution() = processExecution;

  def getStage(): ProcessStage = stages.last;

  def setStage(stage: ProcessStage) = {
    val processName = processExecution.getProcessName();
    logger.debug(s"stage changed: $stage, process: $processName");
    stages += stage
  };

  def sendError(stage: ProcessStage, cause: Throwable) {
    val processName = processExecution.getProcessName();
    val jee = new JobExecutionException(s"failed to execute process: $processName", cause);
    logger.error {
      s"failed to execute process: $processName, stage: $stage, cause: $cause"
    };
    errorHandler.handle(jee);
    throw jee;
  }

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
}

class ProcessAsQuartzJob extends Job with Logging {
  override def execute(context: JobExecutionContext): Unit = {
    val map = context.getJobDetail.getJobDataMap;
    val processName = map.get("processName").asInstanceOf[String];
    val executionContext = context.getScheduler.getContext.get("executionContext").asInstanceOf[FlowExecutionContext];

    val pe = executionContext.runProcess(processName);

    pe.start();
    context.setResult(true);
  }
}

class ProcessExecutionImpl(processName: String, process: Process, executionContext: FlowExecutionContext)
  extends ProcessExecution with Logging {
  val id = "process_excution_" + IdGenerator.nextId[ProcessExecution];
  val processExecutionContext = createContext();

  override def getId(): String = id;

  override def start(): Unit = {
    try {
      //prepare()
      processExecutionContext.setStage(PrepareStart());
      process.onPrepare(processExecutionContext);
      processExecutionContext.setStage(PrepareComplete());
    }
    catch {
      case e: Throwable =>
        try {
          //rollback()
          logger.warn(s"onPrepare() failed: $e");
          e.printStackTrace();

          processExecutionContext.setStage(RollbackStart());
          process.onRollback(processExecutionContext);
          processExecutionContext.setStage(RollbackComplete());
        }
        catch {
          case e: Throwable =>
            logger.warn(s"onRollback() failed: $e");
            processExecutionContext.sendError(RollbackStart(), e);
            e.printStackTrace();
            throw e;
        }
    }

    try {
      //commit()
      processExecutionContext.setStage(CommitStart());
      process.onCommit(processExecutionContext);
      processExecutionContext.setStage(CommitComplete());
    }
    catch {
      case e: Throwable =>
        logger.warn(s"onCommit() failed: $e");
        processExecutionContext.sendError(CommitStart(), e);
        e.printStackTrace();
        throw e;
    }
  }

  override def getProcessName(): String = processName;

  override def getProcess(): Process = process;

  private def createContext() =
    new ProcessExecutionContextImpl(this, executionContext);
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