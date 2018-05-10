package cn.piflow

import cn.piflow.util.Logging
import scala.collection.mutable.{ArrayBuffer, Map => MMap}

trait Event {

}

trait EventHandler {
  def handle(event: Event, args: Any): Unit;
}

trait EventEmiter {
  def fire(event: Event, args: Any): Unit;

  def on(event: Event, handler: EventHandler): Unit;
}

class EventEmiterImpl extends EventEmiter with Logging {
  val listeners = MMap[Event, ArrayBuffer[EventHandler]]();

  def on(event: Event, handler: EventHandler): Unit = {
    if (!listeners.contains(event))
      listeners += event -> ArrayBuffer[EventHandler]();

    listeners(event) += handler;
    logger.debug(s"listening on $event, listener: $handler");
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