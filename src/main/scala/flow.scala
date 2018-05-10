package cn.piflow

import java.util.concurrent.atomic.AtomicInteger

import cn.piflow.util.Logging
import org.quartz.Trigger.CompletedExecutionInstruction
import org.quartz.impl.StdSchedulerFactory
import org.quartz.{Trigger => QuartzTrigger, _}

import scala.collection.JavaConversions._
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

/**
  * Created by bluejoe on 2018/5/2.
  */
class Flow {
  val triggers = ArrayBuffer[Trigger]();
  val processes = MMap[String, Process]();

  def addProcess(name: String, process: Process) = {
    processes(name) = process;
    this;
  };

  def addTrigger(trigger: Trigger) = {
    triggers += trigger;
    this;
  }

  def getProcess(name: String) = processes(name);

  def getTriggers() = triggers.toSeq;
}

object Runner {
  val idgen = new AtomicInteger();

  def run(flow: Flow, args: Map[String, Any] = Map()): FlowExecution = {
    new FlowExecutionImpl("" + idgen.incrementAndGet(), flow, args);
  }
}

trait FlowExecution {
  def addListener(listener: FlowExecutionListener);

  def getId(): String;

  def start(starts: String*);

  def getContext(): ExecutionContext;

  def getFlow(): Flow;

  def stop();

  def getRunningProcesses(): Seq[(String, String)];
}

trait Process {
  def run(pc: ProcessContext);
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

trait ExecutionContext extends Context with EventEmiter {
  def getFlow(): Flow;

  def scheduleProcessRepeatly(cronExpr: String, processName: String): Unit;
}

class ProcessContext(executionContext: ExecutionContext) extends Context {
  val context = MMap[String, Any]();

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

  def getExecutionContext(): ExecutionContext = executionContext;
}

class FlowExecutionImpl(id: String, flow: Flow, args: Map[String, Any])
  extends FlowExecution with Logging {
  def start(starts: String*): Unit = {
    //set context
    args.foreach { (en) =>
      executionContext.put(en._1, en._2);
    };

    //activates all triggers
    triggers.foreach(_.activate(executionContext));

    quartzScheduler.start();

    //runs start processes
    starts.foreach { processName =>
      executionContext.fire(LaunchProcess(), processName);
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

  val executionContext = new EventEmiterImpl() with ExecutionContext {
    //listens on LaunchProcess
    this.on(LaunchProcess(), new EventHandler() {
      override def handle(event: Event, args: Any): Unit = {
        scheduleProcess(args.asInstanceOf[String]);
      }
    });

    val context = MMap[String, Any]();

    def get(key: String): Any = context(key);

    def put(key: String, value: Any) = {
      context(key) = value;
      this;
    }

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

    def scheduleProcess(processName: String): Unit = {
      _scheduleProcess(processName);
    }

    override def scheduleProcessRepeatly(processName: String, cronExpr: String): Unit = {
      _scheduleProcess(processName, Some(CronScheduleBuilder.cronSchedule(cronExpr)));
    }

    override def getFlow(): Flow = flow;
  };

  val quartzScheduler = StdSchedulerFactory.getDefaultScheduler();
  quartzScheduler.getContext.put("executionContext", executionContext);
  val triggers = flow.getTriggers();
  val listeners = ArrayBuffer[FlowExecutionListener]();

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

  override def getContext() = executionContext;

  override def getId(): String = id;

  override def addListener(listener: FlowExecutionListener): Unit = listeners += listener;

  override def getFlow(): Flow = flow;
}

case class LaunchProcess() extends Event {
}

case class ProcessStarted(processName: String) extends Event {
}

case class ProcessFailed(processName: String) extends Event {
}

case class ProcessCompleted(processName: String) extends Event {
}

class ProcessAsQuartzJob extends Job with Logging {
  override def execute(context: JobExecutionContext): Unit = {
    val map = context.getJobDetail.getJobDataMap;
    val processName = map.get("processName").asInstanceOf[String];
    val executionContext = context.getScheduler.getContext.get("executionContext").asInstanceOf[ExecutionContext];
    try {
      executionContext.getFlow().getProcess(processName)
        .run(new ProcessContext(executionContext));
      context.setResult(true);
    }
    catch {
      case e: Throwable =>
        e.printStackTrace();
        throw new JobExecutionException(s"failed to execute process: $processName", e);
    }
  }
}