package cn.piflow

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