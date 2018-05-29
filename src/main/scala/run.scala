/**
  * Created by bluejoe on 2018/5/28.
  */
package cn.piflow

import cn.piflow.ProcessStages.ProcessStage
import cn.piflow.util.{IdGenerator, Logging}
import org.quartz.Trigger.CompletedExecutionInstruction
import org.quartz.impl.StdSchedulerFactory
import org.quartz.{Trigger => QuartzTrigger, _}

import scala.collection.JavaConversions._
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

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

  def getId(): String;

  def start(starts: String*);

  def getFlow(): Flow;

  def stop();

  def getRunningProcesses(): Seq[(String, String)];
}

trait FlowExecutionContext extends Context with EventEmiter {
  def getFlow(): Flow;

  def getFlowExecution(): FlowExecution;
}

class FlowExecutionGraph {

}

class FlowExecutionImpl(flow: Flow, runnerContext: Context)
  extends FlowExecution with Logging {
  val id = "flow_excution_" + IdGenerator.nextId[FlowExecution];
  val graph = new FlowExecutionGraph();
  val execution = this;
  val executionContext = createContext(runnerContext);
  val quartzScheduler = StdSchedulerFactory.getDefaultScheduler();
  val listeners = ArrayBuffer[FlowExecutionListener]();

  def start(starts: String*): Unit = {
    //activates all triggers
    flow.getProcessNames().foreach { name =>
      flow.getTriggers(name).foreach { trigger =>
        trigger.activate(name, executionContext);
      }
    }

    quartzScheduler.start();

    //runs start processes
    starts.foreach { processName =>
      executionContext.fire(LaunchProcess(processName));
    }
  }

  def stop() = {
    quartzScheduler.shutdown();
  }

  override def getRunningProcesses(): Seq[(String, String)] = {
    quartzScheduler.getCurrentlyExecutingJobs()
      .map { jec: JobExecutionContext =>
        (jec.getFireInstanceId,
          jec.getJobDetail.getJobDataMap.get("processName").asInstanceOf[String])
      };
  }

  quartzScheduler.getContext.put("executionContext", executionContext);

  override def getId(): String = id;

  quartzScheduler.getListenerManager.addTriggerListener(new TriggerListener {
    override def vetoJobExecution(trigger: QuartzTrigger, context: JobExecutionContext): Boolean = false;

    override def triggerFired(trigger: QuartzTrigger, context: JobExecutionContext): Unit = {
      val map = context.getJobDetail.getJobDataMap;
      val processName = map.get("processName").asInstanceOf[String];
      logger.debug(s"process started: $processName");

      executionContext.fire(ProcessStarted(processName));
    }

    override def getName: String = this.getClass.getName;

    override def triggerMisfired(trigger: QuartzTrigger): Unit = {}

    override def triggerComplete(trigger: QuartzTrigger, context: JobExecutionContext, triggerInstructionCode: CompletedExecutionInstruction): Unit = {
      val map = context.getJobDetail.getJobDataMap;
      val processName = map.get("processName").asInstanceOf[String];

      val result = context.getResult;
      if (true == result) {
        logger.debug(s"process completed: $processName");
        executionContext.fire(ProcessCompleted(processName));
      }
      else {
        logger.debug(s"process failed: $processName");
        executionContext.fire(ProcessFailed(processName));
      }
    }
  });

  override def addListener(listener: FlowExecutionListener): Unit =
    listeners += listener;

  override def getFlow(): Flow = flow;

  private def createContext(runnerContext: Context): FlowExecutionContext = {
    new CascadeContext(runnerContext)
      with EventEmiter
      with FlowExecutionContext {

      //listens on LaunchProcess
      this.on(classOf[LaunchProcess], new EventHandler() {
        override def handle(event: Event): Unit = {
          _scheduleProcess(event.asInstanceOf[LaunchProcess].processName);
        }
      });

      //listens on CronProcess
      this.on(classOf[CronProcess], new EventHandler() {
        override def handle(event: Event): Unit = {
          _scheduleProcess(event.asInstanceOf[CronProcess].processName,
            Some(CronScheduleBuilder.cronSchedule(event.asInstanceOf[CronProcess].cronExpr)));
        }
      });

      private def _scheduleProcess(processName: String, scheduleBuilder: Option[ScheduleBuilder[_]] = None): Unit = {
        val quartzTriggerBuilder = TriggerBuilder.newTrigger().startNow();
        if (scheduleBuilder.isDefined) {
          quartzTriggerBuilder.withSchedule(scheduleBuilder.get)
        };

        val quartzTrigger = quartzTriggerBuilder.build();

        val quartzJob = JobBuilder.newJob(classOf[ProcessAsQuartzJob])
          .usingJobData("processName", processName)
          .build();

        logger.debug(s"scheduled process: $processName");
        quartzScheduler.scheduleJob(quartzJob, quartzTrigger);
      }

      override def getFlow(): Flow = flow;

      override def getFlowExecution(): FlowExecution = execution;
    };
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

class ProcessExecutionContextImpl(processExecution: ProcessExecution, flowExecutionContext: FlowExecutionContext)
  extends CascadeContext(flowExecutionContext)
    with ProcessExecutionContext
    with Logging {
  val stages = ArrayBuffer[ProcessStage]();
  var errorHandler: ErrorHandler = ErrorHandler.Noop;

  def getProcessExecution() = processExecution;

  def getStage(): ProcessStage = stages.last;

  def setStage(stage: ProcessStage) = {
    val processName = processExecution.getProcessName();
    logger.debug(s"----$stage($processName)----");
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
}

class ProcessAsQuartzJob extends Job with Logging {
  override def execute(context: JobExecutionContext): Unit = {
    val map = context.getJobDetail.getJobDataMap;
    val processName = map.get("processName").asInstanceOf[String];
    val executionContext = context.getScheduler.getContext.get("executionContext").asInstanceOf[FlowExecutionContext];
    new ProcessExecutionImpl(processName, executionContext.getFlow().getProcess(processName), executionContext).start();
    context.setResult(true);
  }
}

class ProcessExecutionImpl(processName: String, process: Process, flowExecutionContext: FlowExecutionContext)
  extends ProcessExecution with Logging {
  val id = "process_excution_" + IdGenerator.nextId[ProcessExecution];
  val pec = createContext();

  override def getId(): String = id;

  override def start(): Unit = {
    var shadow: Shadow = null;
    try {
      pec.setStage(ProcessStages.PREPARING);
      shadow = process.shadow(pec);
      pec.setStage(ProcessStages.PREPARED);
      pec.setStage(ProcessStages.PERFORMING);
      shadow.perform(pec);
      pec.setStage(ProcessStages.PERFORMED);
      pec.setStage(ProcessStages.COMMITING);
      shadow.commit(pec);
      pec.setStage(ProcessStages.COMMITED);
    }
    catch {
      case e: Throwable =>
        try {
          //rollback()
          logger.warn(s"commit() failed: $e");
          e.printStackTrace();
          shadow.discard(pec);
          pec.setStage(ProcessStages.DISCARDED);
        }
        catch {
          case e: Throwable =>
            logger.warn(s"discard() failed: $e");
            pec.sendError(ProcessStages.DISCARDING, e);
            e.printStackTrace();
            throw e;
        }
    }
  }

  override def getProcessName(): String = processName;

  override def getProcess(): Process = process;

  private def createContext() =
    new ProcessExecutionContextImpl(this, flowExecutionContext);
}

object ProcessStages extends Enumeration {
  type ProcessStage = Value;

  val PREPARING = Value("PREPARING");
  val PREPARED = Value("PREPARED");
  val PERFORMING = Value("PERFORMING");
  val PERFORMED = Value("PERFORMED");
  val COMMITING = Value("COMMITING");
  val COMMITED = Value("COMMITED");
  val DISCARDING = Value("DISCARDING");
  val DISCARDED = Value("DISCARDED");
}