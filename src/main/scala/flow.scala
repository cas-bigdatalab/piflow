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

/**
  * start process while dependent processes completed
  */
object DependencyTrigger {
  def dependency(processName: String, dependentProcesses: String*): Trigger = new Trigger() {
    override def activate(executionContext: ExecutionContext): Unit = {
      val listener = new EventListener {
        var fired = false;
        val completed = MMap[String, Boolean]();
        dependentProcesses.foreach { processName =>
          completed(processName) = false;
        };

        def handle(event: Event, args: Any) {
          completed(event.asInstanceOf[ProcessCompleted].processName) = true;

          if (completed.values.filter(!_).isEmpty) {
            fired = true;
            executionContext.fire(LaunchProcess(), processName);
          }
        }
      };

      dependentProcesses.foreach { dependency =>
        executionContext.on(ProcessCompleted(dependency), listener);
      }
    }

    override def getTriggeredProcesses(): Seq[String] = Seq(processName);
  }
}

/**
  * start processes repeatedly
  */
object TimerTrigger {
  def cron(cronExpr: String, processNames: String*): Trigger = new Trigger() {
    override def activate(context: ExecutionContext): Unit = {
      processNames.foreach { processName =>
        context.scheduleProcessCronly(processName, cronExpr);
      }
    }

    override def getTriggeredProcesses(): Seq[String] = processNames;
  }
}

/**
  * start processes while Events happen
  */
object EventTrigger {
  def listen(event: Event, processNames: String*): Trigger = new Trigger() {
    override def activate(context: ExecutionContext): Unit = {
      processNames.foreach { processName =>
        context.on(event, new EventListener() {
          override def handle(event: Event, args: Any): Unit = {
            context.scheduleProcess(processName);
          }
        });
      }
    }

    override def getTriggeredProcesses(): Seq[String] = processNames;
  }
}

trait Execution {

  def stop();

  def getRunningProcesses(): Seq[(String, String)];

  def getScheduledProcesses(): Seq[String];

}

trait Runner {
  def run(flow: Flow, starts: String*): Execution;
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

  def scheduleProcess(name: String): Unit;

  def scheduleProcessCronly(cronExpr: String, processName: String): Unit;
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

class ExecutionImpl(flow: Flow, starts: Seq[String]) extends Execution with Logging {
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

    override def scheduleProcess(processName: String): Unit = {
      _scheduleProcess(processName);
    }

    override def scheduleProcessCronly(processName: String, cronExpr: String): Unit = {
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