package cn.piflow

import scala.collection.mutable.{Map => MMap}

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
  def declareDependency(processName: String, dependentProcesses: String*): Trigger = new Trigger() {
    override def activate(executionContext: ExecutionContext): Unit = {
      val listener = new EventListener {
        val completed = MMap[String, Boolean]();
        dependentProcesses.foreach { processName =>
          completed(processName) = false;
        };

        def handle(event: Event, args: Any) {
          completed(event.asInstanceOf[ProcessCompleted].processName) = true;

          if (completed.values.filter(!_).isEmpty) {
            completed.clear();
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
    override def activate(executionContext: ExecutionContext): Unit = {
      processNames.foreach { processName =>
        executionContext.scheduleProcessRepeatly(processName, cronExpr);
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
    override def activate(executionContext: ExecutionContext): Unit = {
      processNames.foreach { processName =>
        executionContext.on(event, new EventListener() {
          override def handle(event: Event, args: Any): Unit = {
            executionContext.fire(LaunchProcess(), processName);
          }
        });
      }
    }

    override def getTriggeredProcesses(): Seq[String] = processNames;
  }
}
