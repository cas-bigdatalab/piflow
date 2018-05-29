package cn.piflow

import cn.piflow.util.Logging

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

trait Event {
  /**
    * key is used to capture events of this type
    *
    * @return
    */
  def key(): Any;
}

case class LaunchProcess(processName: String) extends Event {
  def key() = this.getClass;
}

case class CronProcess(processName: String, cronExpr: String) extends Event {
  def key() = this.getClass;
}

case class ProcessStarted(processName: String) extends Event {
  def key() = this;
}

case class ProcessFailed(processName: String) extends Event {
  def key() = this;
}

case class ProcessCompleted(processName: String) extends Event {
  def key() = this;
}

trait EventHandler {
  def handle(event: Event): Unit;
}

trait EventEmiter extends Logging {
  val listeners = MMap[Any, ArrayBuffer[EventHandler]]();

  def on(eventKey: Any, handler: EventHandler): Unit = {
    if (!listeners.contains(eventKey))
      listeners += eventKey -> ArrayBuffer[EventHandler]();

    listeners(eventKey) += handler;
    logger.debug(s"listening on $eventKey, listener: $handler");
  }

  def fire[T](event: Event): Unit = {
    logger.debug(s"fired event: $event");
    val eventKey = event.key();
    if (listeners.contains(eventKey)) {
      for (listener <- listeners(eventKey)) {
        logger.debug(s"handling event: $event, listener: $listener");
        listener.asInstanceOf[EventHandler].handle(event);
        logger.debug(s"handled event: $event, listener: $listener");
      }
    }
  }
}