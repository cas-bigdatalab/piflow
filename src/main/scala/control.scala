package cn.piflow

import cn.piflow.util.Logging
import org.quartz._
import org.quartz.impl.StdSchedulerFactory

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

/**
  * Created by bluejoe on 2018/5/2.
  */

trait Chain {
  def addProcess(name: String, process: Process): Chain;

  def trigger(name: String, trigger: Trigger): Chain;

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

  def satisfied(context: ExecutionContext): Boolean;

  def stop(context: ExecutionContext);
}

abstract class AbstractBoundTrigger(name: String, process: Process) extends BoundTrigger {
  def start(context: ExecutionContext) {}

  def getProcessName() = name;

  def getProcess() = process;

  def satisfied(context: ExecutionContext): Boolean;

  def stop(context: ExecutionContext) {}
}

object SequenceTriggerBuilder {

  class SequenceTrigger(predecessors: Seq[String]) extends Trigger {
    val dps = predecessors.distinct;

    override def bind(name: String, process: Process): BoundTrigger = new AbstractBoundTrigger(name, process) {
      override def satisfied(context: ExecutionContext): Boolean = {
        val completed = context.getCompletedProcesses();
        //all predecessors are completed?
        predecessors.filter(completed.contains(_)).distinct.size == dps.size
      };
    }
  }

  def after(predecessors: String*): Trigger = new SequenceTrigger(predecessors);
}

object TimerTriggerBuilder {

  class TimerTrigger(cronExpr: String) extends Trigger {
    override def bind(name: String, process: Process): BoundTrigger = new AbstractBoundTrigger(name, process) {
      override def start(context: ExecutionContext): Unit = {
        context.scheduleProcess(name, process, cronExpr);
      }

      override def satisfied(context: ExecutionContext): Boolean = false;
    }
  }

  def cron(expr: String): Trigger = new TimerTrigger(expr);
}

trait Execution {
  def awaitComplete();
}

trait Runner {
  def run(chain: Chain, starts: String*): Execution;

  def run(chain: Chain): Execution;
}

trait ProcessContext {

}

trait Process {
  def run(pc: ProcessContext);
}

class ChainImpl extends Chain {
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
  def run(chain: Chain, starts: String*): Execution = {
    new ExecutionImpl(chain.asInstanceOf[ChainImpl], starts);
  }

  def run(chain: Chain): Execution = {
    new ExecutionImpl(chain.asInstanceOf[ChainImpl], Seq());
  }
}

trait ExecutionContext {
  def scheduleProcess(name: String, process: Process, cronExpr: String);

  def getCompletedProcesses(): Seq[String];
}

class ExecutionImpl(chain: Chain, starts: Seq[String]) extends Execution with Logging {
  def awaitComplete() = {
    val triggers = ArrayBuffer[BoundTrigger]();
    triggers ++= starts.map(name => new InstantTrigger(name, chain.getProcess(name)));
    triggers ++= chain.getTriggers();
    val scheduler = StdSchedulerFactory.getDefaultScheduler();
    scheduler.start();

    val completed = ArrayBuffer[String]();

    val ec = new ExecutionContext() {
      override def scheduleProcess(name: String, process: Process, cronExpr: String): Unit = {
        val quartzTrigger = TriggerBuilder.newTrigger()
          .startNow()
          .withSchedule(CronScheduleBuilder.cronSchedule(cronExpr)
          ).build();

        val quartzJob = JobBuilder.newJob(classOf[ProcessAsQuartzJob])
          .usingJobData("processName", name)
          .build();
        quartzJob.getJobDataMap.put("process", process);
        scheduler.scheduleJob(quartzJob, quartzTrigger);
      };

      override def getCompletedProcesses(): Seq[String] = completed.toSeq;
    };

    triggers.foreach(_.start(ec));

    var head = triggers.filter(_.satisfied(ec)).headOption;
    while (!head.isEmpty) {
      val trigger = head.get;
      val processName = trigger.getProcessName();
      logger.info(s"started process: $processName");
      trigger.getProcess().run(null);
      logger.info(s"finished process: $processName");
      completed += processName;

      head = triggers.filter { trigger =>
        !completed.contains(trigger.getProcessName()) && trigger.satisfied(ec)
      }.headOption;
    }

    triggers.foreach(_.stop(ec));
    scheduler.shutdown();
  }
}

class InstantTrigger(name: String, process: Process) extends AbstractBoundTrigger(name, process) {
  override def satisfied(context: ExecutionContext): Boolean = true;
}

class ProcessAsQuartzJob extends Job with Logging {
  override def execute(context: JobExecutionContext): Unit = {
    val map = context.getJobDetail.getJobDataMap;
    val processName = map.get("processName");

    logger.info(s"started process: $processName");
    map.get("process").asInstanceOf[Process].run(null);
    logger.info(s"finished process: $processName");
  }
}