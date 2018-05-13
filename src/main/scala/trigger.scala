package cn.piflow

import scala.collection.mutable.{Map => MMap}

trait Trigger {
  /**
    * start current trigger on given process
    *
    * @param processName
    * @param context
    */
  def activate(processName: String, context: FlowExecutionContext): Unit;
}

/**
  * start process while dependent processes completed
  */
class DependencyTrigger(dependentProcesses: String*) extends Trigger {
  override def activate(processName: String, executionContext: FlowExecutionContext): Unit = {
    val listener = new EventHandler {
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
}

/**
  * start processes repeatedly
  */
class TimerTrigger(cronExpr: String, processNames: String*) extends Trigger {
  override def activate(processName: String, executionContext: FlowExecutionContext): Unit = {
    processNames.foreach { processName =>
      executionContext.scheduleProcessRepeatly(processName, cronExpr);
    }
  }
}

/**
  * start processes while Events happen
  */
class EventTrigger(event: Event, processNames: String*) extends Trigger {
  override def activate(processName: String, executionContext: FlowExecutionContext): Unit = {
    processNames.foreach { processName =>
      executionContext.on(event, new EventHandler() {
        override def handle(event: Event, args: Any): Unit = {
          executionContext.fire(LaunchProcess(), processName);
        }
      });
    }
  }
}
