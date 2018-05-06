package cn.piflow

import cn.piflow.util.Logging
import org.quartz.Trigger.CompletedExecutionInstruction
import org.quartz.impl.StdSchedulerFactory
import org.quartz.{Trigger => QuartzTrigger, _}

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

/**
  * Created by bluejoe on 2018/5/2.
  */

trait Flow {
  def addProcess(name: String, process: Process): Flow;

  def addTrigger(trigger: Trigger): Flow;

  def getProcess(name: String): Process;

  def getTriggers(): Seq[Trigger];
}

trait Trigger {
  def activate(context: ExecutionContext): Unit;

  def getTriggeredProcesses(): Seq[String];
}

trait Event {

}

case class ProcessCompletedListener(boundProcessName: String, executionContext: ExecutionContext, predecessors: String*) extends EventListener {
  val dps = predecessors.distinct;
  var fired = false;
  val completed = MMap[String, Boolean]();
  dps.foreach { processName =>
    completed(processName) = false;
  };

  def handle(event: Event, args: Any) {
    completed(event.asInstanceOf[ProcessCompleted].processName) = true;

    if (completed.values.filter(!_).isEmpty) {
      fired = true;
      executionContext.fire(LaunchProcess(), boundProcessName);
    }
  }
}

object DependencyTrigger {
  def dependOn(triggeredProcessName: String, dependencies: String*): Trigger = new Trigger() {
    override def activate(context: ExecutionContext): Unit = {
      val listener = new ProcessCompletedListener(triggeredProcessName, context, dependencies: _*);
      dependencies.foreach { dependency =>
        context.on(ProcessCompleted(dependency), listener);
      }
    }

    override def getTriggeredProcesses(): Seq[String] = Seq(triggeredProcessName);
  }
}

object CronTrigger {
  def cron(cronExpr: String, processNames: String*): Trigger = new Trigger() {
    override def activate(context: ExecutionContext): Unit = {
      processNames.foreach { processName =>
        context.cronProcess(processName, cronExpr);
      }
    }

    override def getTriggeredProcesses(): Seq[String] = processNames;
  }
}

trait Execution {
  def start();

  def stop();
}

trait Runner {
  def run(chain: Flow, starts: String*): Execution;
}

trait ProcessContext {

}

trait Process {
  def run(pc: ProcessContext);
}

class FlowImpl extends Flow {
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

class RunnerImpl extends Runner {
  def run(flow: Flow, starts: String*): Execution = {
    val execution = new ExecutionImpl(flow, starts);
    execution.start();
    execution;
  }
}

trait EventListener {
  def handle(event: Event, args: Any): Unit;
}

trait EventEmiter {
  def fire(event: Event, args: Any): Unit;

  def on(event: Event, listener: EventListener): Unit;
}

trait ExecutionContext extends EventEmiter {
  def getFlow(): Flow;

  def startProcess(name: String): Unit;

  def cronProcess(cronExpr: String, processName: String): Unit;
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

case class LaunchProcessListener(executionContext: ExecutionContext) extends EventListener {
  def handle(event: Event, args: Any) {
    executionContext.startProcess(args.asInstanceOf[String]);
  }
}

class ExecutionImpl(flow: Flow, starts: Seq[String]) extends Execution with Logging {

  val executionContext = new EventEmiterImpl() with ExecutionContext {
    //listens on LaunchProcess
    this.on(LaunchProcess(), new LaunchProcessListener(this));

    override def startProcess(processName: String): Unit = {
      val quartzTrigger = TriggerBuilder.newTrigger().startNow()
        .build();

      val quartzJob = JobBuilder.newJob(classOf[ProcessAsQuartzJob])
        .usingJobData("processName", processName)
        .build();

      quartzScheduler.scheduleJob(quartzJob, quartzTrigger);
    }

    override def cronProcess(processName: String, cronExpr: String): Unit = {
      val quartzTrigger = TriggerBuilder.newTrigger().startNow()
        .withSchedule(CronScheduleBuilder.cronSchedule(cronExpr))
        .build();

      val quartzJob = JobBuilder.newJob(classOf[CronAsQuartzJob])
        .usingJobData("processName", processName)
        .build();

      quartzScheduler.scheduleJob(quartzJob, quartzTrigger);
    }

    override def getFlow(): Flow = flow;
  };

  def start(): Unit = {
    triggers.foreach(_.activate(executionContext));
    quartzScheduler.start();
    starts.foreach { processName =>
      executionContext.fire(LaunchProcess(), processName);
    }
  }

  def stop() = {
    quartzScheduler.shutdown();
  }

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
      logger.debug(s"process completed: $processName");

      //notify all triggers
      executionContext.fire(ProcessCompleted(processName));
    }
  });
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
    executionContext.getFlow().getProcess(processName).run(null);
  }
}

class CronAsQuartzJob extends Job with Logging {
  override def execute(context: JobExecutionContext): Unit = {
    val map = context.getJobDetail.getJobDataMap;
    val processName = map.get("processName").asInstanceOf[String];
    val executionContext = context.getScheduler.getContext.get("executionContext").asInstanceOf[ExecutionContext];
    executionContext.fire(LaunchProcess(), processName);
  }
}