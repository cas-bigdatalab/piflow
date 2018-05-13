package cn.piflow

import cn.piflow.util.{IdGenerator, Logging}
import org.quartz.Trigger.CompletedExecutionInstruction
import org.quartz.impl.StdSchedulerFactory
import org.quartz.{Trigger => QuartzTrigger, _}

import scala.collection.JavaConversions._
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

/**
  * Created by bluejoe on 2018/5/2.
  */

trait Flow {
  def getProcessNames(): Seq[String];

  def addProcess(name: String, process: Process): Flow;

  def addTrigger(processName: String, trigger: Trigger): Flow;

  def getProcess(name: String): Process;

  def getTriggers(processName: String): Seq[Trigger];
}

class FlowImpl extends Flow {
  val triggers = MMap[String, ArrayBuffer[Trigger]]();
  val processes = MMap[String, Process]();

  def addProcess(name: String, process: Process) = {
    processes(name) = process;
    this;
  };

  def addTrigger(processName: String, trigger: Trigger) = {
    val processTriggers = triggers.getOrElseUpdate(processName, ArrayBuffer[Trigger]());
    processTriggers += trigger;
    this;
  }

  def getProcess(name: String) = processes(name);

  def getTriggers(processName: String) = triggers.getOrElse(processName, ArrayBuffer[Trigger]()).toSeq;

  override def getProcessNames(): Seq[String] = processes.map(_._1).toSeq;
}

object Runner {
  def run(flow: Flow, args: Map[String, Any] = Map()): FlowExecution = {
    new FlowExecutionImpl(flow, args);
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

trait Context {
  def get(key: String): Any;

  def get[T]()(implicit m: Manifest[T]): T = {
    get(m.runtimeClass.getName).asInstanceOf[T];
  }

  def put(key: String, value: Any): this.type;

  def put[T](value: T)(implicit m: Manifest[T]): this.type =
    put(m.runtimeClass.getName, value);
}

trait FlowExecutionContext extends Context with EventEmiter {
  def getFlow(): Flow;

  def runProcess(processName: String): ProcessExecution;

  def getFlowExecution(): FlowExecution;

  def scheduleProcessRepeatly(cronExpr: String, processName: String): Unit;
}

class FlowExecutionImpl(flow: Flow, args: Map[String, Any])
  extends FlowExecution with Logging {
  val id = "flow_excution_" + IdGenerator.nextId[FlowExecution];

  val execution = this;
  val executionContext = createContext();
  val quartzScheduler = StdSchedulerFactory.getDefaultScheduler();
  val listeners = ArrayBuffer[FlowExecutionListener]();

  def start(starts: String*): Unit = {
    //set context
    args.foreach { (en) =>
      executionContext.put(en._1, en._2);
    };

    //activates all triggers
    flow.getProcessNames().foreach { name =>
      flow.getTriggers(name).foreach { trigger =>
        trigger.activate(name, executionContext);
      }
    }

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

  private def createContext(): FlowExecutionContext = {
    new EventEmiterImpl() with FlowExecutionContext {
      //listens on LaunchProcess
      this.on(LaunchProcess(), new EventHandler() {
        override def handle(event: Event, args: Any): Unit = {
          scheduleProcess(args.asInstanceOf[String]);
        }
      });

      val context = MMap[String, Any]();

      def get(key: String): Any = context(key);

      def runProcess(processName: String): ProcessExecution = {
        new ProcessExecutionImpl(processName, flow.getProcess(processName), executionContext);
      }

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

      override def getFlowExecution(): FlowExecution = execution;
    };
  }
}
