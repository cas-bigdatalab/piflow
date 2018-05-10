package cn.piflow

import cn.piflow.util.Logging
import org.quartz.Trigger.CompletedExecutionInstruction
import org.quartz.impl.StdSchedulerFactory
import org.quartz.impl.matchers.GroupMatcher
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

class Runner {
  def run(flow: Flow, starts: String*): FlowExecution = {
    new FlowExecutionImpl(flow, starts);
  }
}

trait FlowExecution {
  def start(args: Map[String, Any] = Map());

  def getContext(): ExecutionContext;

  def stop();

  def getRunningProcesses(): Seq[(String, String)];

  def getScheduledProcesses(): Seq[String];

}

trait Process {
  def run(pc: ProcessContext);
}

trait EventListener {
  def handle(event: Event, args: Any): Unit;
}

trait EventEmiter {
  def fire(event: Event, args: Any): Unit;

  def on(event: Event, listener: EventListener): Unit;
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

class EventEmiterImpl extends EventEmiter with Logging {
  val listeners = MMap[Event, ArrayBuffer[EventListener]]();

  def on(event: Event, listener: EventListener): Unit = {
    if (!listeners.contains(event))
      listeners += event -> ArrayBuffer[EventListener]();

    listeners(event) += listener;
    logger.debug(s"listening on $event, listener: $listener");
  }

  def fire(event: Event, args: Any = None): Unit = {
    logger.debug(s"fired event: $event, args: $args");
    if (listeners.contains(event)) {
      for (listener <- listeners(event)) {
        logger.debug(s"handling event: $event, args: $args, listener: $listener");
        listener.handle(event, args);
        logger.debug(s"handled event: $event, args: $args, listener: $listener");
      }
    }
  }
}

class FlowExecutionImpl(flow: Flow, starts: Seq[String]) extends FlowExecution with Logging {
  def start(args: Map[String, Any]): Unit = {
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

  def getRunningProcesses(): Seq[(String, String)] = {
    quartzScheduler.getCurrentlyExecutingJobs()
      .map { jec: JobExecutionContext =>
        (jec.getFireInstanceId,
          jec.getJobDetail.getJobDataMap.get("processName").asInstanceOf[String])
      };
  }

  def getScheduledProcesses(): Seq[String] = {
    quartzScheduler.getJobKeys(GroupMatcher.anyGroup())
      .map(quartzScheduler.getJobDetail(_))
      .map(_.getJobDataMap.get("processName").asInstanceOf[String])
      .toSeq;
  }

  val executionContext = new EventEmiterImpl() with ExecutionContext {
    //listens on LaunchProcess
    this.on(LaunchProcess(), new EventListener() {
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
    }
  });

  override def getContext() = executionContext;
}

case class LaunchProcess() extends Event {
}

case class ProcessStarted(processName: String) extends Event {
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
        logger.warn(s"failed to execute process: $processName, cause: $e");
        e.printStackTrace();
        throw new JobExecutionException(s"failed to execute process: $processName", e);
    }
  }
}