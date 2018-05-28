package cn.piflow

import org.quartz._

import scala.collection.mutable.{Map => MMap}

trait Process {
  /**
    * shadow is used to assure being Atomic
    *
    * @param pec
    * @return
    */
  def shadow(pec: ProcessExecutionContext): Shadow;

  /**
    * Backup is used to perform undo()
    *
    * @param pec
    * @return
    */
  def backup(pec: ProcessExecutionContext): Backup;
}

trait Backup extends Serializable {
  def undo(pec: ProcessExecutionContext): Unit;
}

trait Shadow {
  def perform(pec: ProcessExecutionContext): Unit;

  def commit(pec: ProcessExecutionContext): Unit;

  def discard(pec: ProcessExecutionContext): Unit;
}

trait ErrorHandler {
  def handle(jee: JobExecutionException);
}

object ErrorHandler {
  val Noop = new ErrorHandler {
    def handle(jee: JobExecutionException): Unit = {
    }
  };

  val Retry = new ErrorHandler {
    def handle(jee: JobExecutionException): Unit = {
      jee.setRefireImmediately(true);
    }
  };

  val Abort = new ErrorHandler {
    def handle(jee: JobExecutionException): Unit = {
      jee.setUnscheduleFiringTrigger(true);
    }
  };

  val Fail = new ErrorHandler {
    def handle(jee: JobExecutionException): Unit = {
      jee.setUnscheduleAllTriggers(true);
    }
  };
}

/**
  * a process that can not be prepared and undoable
  */
trait PartialProcess extends Process {
  def perform(pec: ProcessExecutionContext);
  val process = this;

  def shadow(pec: ProcessExecutionContext): Shadow = new Shadow {
    override def discard(pec: ProcessExecutionContext): Unit = {}

    override def perform(pec: ProcessExecutionContext): Unit = {}

    override def commit(pec: ProcessExecutionContext): Unit = process.perform(pec);
  }

  def backup(pec: ProcessExecutionContext): Backup = {
    null;
  }
}
