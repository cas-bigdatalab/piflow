package cn.piflow

import cn.piflow.util.Logging
import org.quartz.Trigger.CompletedExecutionInstruction
import org.quartz.impl.StdSchedulerFactory
import org.quartz.{Trigger => QuartzTrigger, _}

import scala.collection.mutable.{Map => MMap}

/**
  * Created by bluejoe on 2018/5/2.
  */

trait Flow {
  def addProcess(name: String, process: Process): Flow;

  def trigger(name: String, trigger: Trigger): Flow;

  def getProcess(name: String): Process;

  def getTriggers(): Seq[BoundTrigger];

  def getTrigger(name: String): BoundTrigger;
}

trait Trigger {
  def bind(name: String, process: Process): BoundTrigger;
}

trait BoundTrigger {
  def start(context: ExecutionContext);

  def getProcessName(): String;

  def getProcess(): Process;

  def onProcessComplete(processName: String, context: ExecutionContext): Unit;

  def stop(context: ExecutionContext);
}

abstract class AbstractBoundTrigger(name: String, process: Process) extends BoundTrigger {
  def start(context: ExecutionContext) {}

  def getProcessName() = name;

  def getProcess() = process;

  def stop(context: ExecutionContext) {}
}

object SequenceTriggerBuilder {

  class SequenceTrigger(predecessors: Seq[String]) extends Trigger {
    val dps = predecessors.distinct;

    val completed = MMap[String, Boolean]();
    dps.foreach { processName =>
      completed(processName) = false;
    };

    override def bind(name: String, process: Process): BoundTrigger = new AbstractBoundTrigger(name, process) {
      override def onProcessComplete(processName: String, context: ExecutionContext): Unit = {
        if (completed.contains(processName))
          completed(processName) = true;

        if (completed.values.filter(!_).isEmpty) {
          context.startProcess(processName);
        }
      }
    }
  }

  def after(predecessors: String*): Trigger = new SequenceTrigger(predecessors);
}

object TimerTriggerBuilder {

  class TimerTrigger(cronExpr: String) extends Trigger {
    override def bind(name: String, process: Process): BoundTrigger = new AbstractBoundTrigger(name, process) {
      override def start(context: ExecutionContext): Unit = {
        context.scheduleProcess(name, cronExpr);
      }

      override def onProcessComplete(processName: String, context: ExecutionContext): Unit = {
      }
    }
  }

  def cron(expr: String): Trigger = new TimerTrigger(expr);
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
  val triggers = MMap[String, BoundTrigger]();
  val processes = MMap[String, Process]();

  def addProcess(name: String, process: Process) = {
    processes(name) = process;
    this;
  };

  def trigger(name: String, trigger: Trigger) = {
    triggers(name) = trigger.bind(name, processes(name));
    this;
  }

  def getProcess(name: String) = processes(name);

  def getTriggers() = triggers.values.toSeq;

  def getTrigger(name: String) = triggers(name);
}

class RunnerImpl extends Runner {
  def run(flow: Flow, starts: String*): Execution = {
    val exe = new ExecutionImpl(flow, starts);
    exe.start();
    exe;
  }
}

trait ExecutionContext {
  def scheduleProcess(name: String, cronExpr: String);

  def startProcess(name: String);
}

class ExecutionImpl(flow: Flow, starts: Seq[String]) extends Execution with Logging {
  def start(): Unit = {
    triggers.foreach(_.start(ec));

    starts.foreach { processName =>
      ec.startProcess(processName);
    };

    quartzScheduler.start();
  }

  def stop() = {
    triggers.foreach(_.stop(ec));
    quartzScheduler.shutdown();
  }

  val quartzScheduler = StdSchedulerFactory.getDefaultScheduler();
  val triggers = flow.getTriggers();

  val ec = new ExecutionContext() {

    private def scheduleProcess(name: String, scheduleBuilder: ScheduleBuilder[CronTrigger] = null): Unit = {
      val builder = TriggerBuilder.newTrigger().startNow();
      if (scheduleBuilder != null)
        builder.withSchedule(scheduleBuilder);

      val quartzTrigger = builder.build();
      val process = flow.getProcess(name);
      val map = new JobDataMap();
      map.put("processName", name);
      map.put("process", process);
      val quartzJob = JobBuilder.newJob(classOf[ProcessAsQuartzJob])
        .setJobData(map)
        .build();

      quartzScheduler.scheduleJob(quartzJob, quartzTrigger);
    }

    override def scheduleProcess(name: String, cronExpr: String): Unit =
      this.scheduleProcess(name, CronScheduleBuilder.cronSchedule(cronExpr));

    override def startProcess(name: String): Unit =
      this.scheduleProcess(name);
  };

  quartzScheduler.getListenerManager.addTriggerListener(new TriggerListener {
    override def vetoJobExecution(trigger: QuartzTrigger, context: JobExecutionContext): Boolean = false;

    override def triggerFired(trigger: QuartzTrigger, context: JobExecutionContext): Unit = {
      val map = context.getJobDetail.getJobDataMap;
      val processName = map.get("processName").asInstanceOf[String];
      logger.info(s"process started: $processName");
    }

    override def getName: String = this.getClass.getName;

    override def triggerMisfired(trigger: QuartzTrigger): Unit = {}

    override def triggerComplete(trigger: QuartzTrigger, context: JobExecutionContext, triggerInstructionCode: CompletedExecutionInstruction): Unit = {
      val map = context.getJobDetail.getJobDataMap;
      val processName = map.get("processName").asInstanceOf[String];
      logger.info(s"process completed: $processName");

      //notify all triggers
      triggers.foreach(_.onProcessComplete(processName, ec));
    }
  });
}

class ProcessAsQuartzJob extends Job with Logging {
  override def execute(context: JobExecutionContext): Unit = {
    val map = context.getJobDetail.getJobDataMap;
    map.get("process").asInstanceOf[Process].run(null);
  }
}