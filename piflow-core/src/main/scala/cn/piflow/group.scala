package cn.piflow

import java.sql.Date
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.{CountDownLatch, TimeUnit}

import scala.collection.mutable.{ArrayBuffer, Map => MMap}

/**
  * Created by bluejoe on 2018/6/27.
  */
trait Condition {
  def matches(pg: FlowGroupExecution): Boolean;
}

class AndCondition(con1: Condition, con2: Condition) extends Condition {
  override def matches(pg: FlowGroupExecution): Boolean = {
    con1.matches(pg) && con2.matches(pg);
  }
}

class OrCondition(con1: Condition, con2: Condition) extends Condition {
  override def matches(pg: FlowGroupExecution): Boolean = {
    con1.matches(pg) || con2.matches(pg);
  }
}

trait ComposableCondition extends Condition {
  def and(others: Condition*): ComposableCondition = {
    new ComposableCondition() {
      override def matches(pg: FlowGroupExecution): Boolean = {
        (this +: others).reduce((x, y) => new AndCondition(x, y)).matches(pg);
      }
    }
  }

  def or(others: Condition*): ComposableCondition = {
    new ComposableCondition() {
      override def matches(pg: FlowGroupExecution): Boolean = {
        (this +: others).reduce((x, y) => new OrCondition(x, y)).matches(pg);
      }
    }
  }
}

object Condition {
  val AlwaysTrue = new Condition() {
    def matches(pg: FlowGroupExecution): Boolean = true;
  }

  def after(processName: String, otherProcessNames: String*) = new ComposableCondition {
    def matches(pg: FlowGroupExecution): Boolean = {
      val processNames = processName +: otherProcessNames;
      return processNames.map(pg.isProcessCompleted(_))
        .filter(_ == true).length == processNames.length;
    }
  }

  def after(when: Date) = new ComposableCondition {
    def matches(pg: FlowGroupExecution): Boolean = {
      return new Date(System.currentTimeMillis()).after(when);
    }
  }
}

trait FlowGroup {
  def addFlow(name: String, flow: Flow, con: Condition = Condition.AlwaysTrue);

  def mapFlowWithConditions(): Map[String, (Flow, Condition)];
}


class FlowGroupImpl extends FlowGroup {
  val _mapFlowWithConditions = MMap[String, (Flow, Condition)]();

  def addFlow(name: String, flow: Flow, con: Condition = Condition.AlwaysTrue) = {
    _mapFlowWithConditions(name) = flow -> con;
  }

  def mapFlowWithConditions(): Map[String, (Flow, Condition)] = _mapFlowWithConditions.toMap;
}

trait FlowGroupExecution {
  def isProcessCompleted(processName: String): Boolean;

  def stop(): Unit;

  def awaitTermination(): Unit;

  def awaitTermination(timeout: Long, unit: TimeUnit): Unit;
}

class FlowGroupExecutionImpl(fg: FlowGroup, runnerContext: Context, runner: Runner) extends FlowGroupExecution {
  val mapFlowWithConditions: Map[String, (Flow, Condition)] = fg.mapFlowWithConditions();
  val completedProcesses = MMap[String, Boolean]();
  completedProcesses ++= mapFlowWithConditions.map(x => (x._1, false));
  val numWaitingProcesses = new AtomicInteger(mapFlowWithConditions.size);
  val startedProcesses = MMap[String, Process]();
  val execution = this;
  val POLLING_INTERVAL = 1000;
  val latch = new CountDownLatch(1);
  var running = true;

  val listener = new RunnerListener {
    override def onProcessStarted(ctx: ProcessContext): Unit = {}

    override def onProcessFailed(ctx: ProcessContext): Unit = {
      //TODO: retry?
    }

    override def onProcessCompleted(ctx: ProcessContext): Unit = {
      startedProcesses.filter(_._2 == ctx.getProcess()).foreach { x =>
        completedProcesses(x._1) = true;
        numWaitingProcesses.decrementAndGet();
      }
    }

    override def onJobStarted(ctx: JobContext): Unit = {}

    override def onJobCompleted(ctx: JobContext): Unit = {}

    override def onJobInitialized(ctx: JobContext): Unit = {}

    override def onProcessForked(ctx: ProcessContext, child: ProcessContext): Unit = {}

    override def onJobFailed(ctx: JobContext): Unit = {}

    override def onProcessAborted(ctx: ProcessContext): Unit = {}

    override def monitorJobCompleted(ctx: JobContext, outputs: JobOutputStream): Unit = {}
  };

  runner.addListener(listener);

  def isProcessCompleted(processName: String): Boolean = {
    completedProcesses(processName);
  }

  private def startProcess(name: String, flow: Flow): Unit = {
    val process = runner.start(flow);
    startedProcesses(name) = process;
  }

  val pollingThread = new Thread(new Runnable() {
    override def run(): Unit = {
      while (numWaitingProcesses.get() > 0) {
        val todos = ArrayBuffer[(String, Flow)]();
        mapFlowWithConditions.foreach { en =>
          if (!startedProcesses.contains(en._1) && en._2._2.matches(execution)) {
            todos += (en._1 -> en._2._1);
          }
        }

        startedProcesses.synchronized {
          todos.foreach(en => startProcess(en._1, en._2));
        }

        Thread.sleep(POLLING_INTERVAL);
      }

      latch.countDown();
      finalizeExecution(true);
    }
  });

  pollingThread.start();

  override def awaitTermination(): Unit = {
    latch.await();
    finalizeExecution(true);
  }

  override def stop(): Unit = {
    finalizeExecution(false);
  }

  override def awaitTermination(timeout: Long, unit: TimeUnit): Unit = {
    if (!latch.await(timeout, unit))
      finalizeExecution(false);
  }

  private def finalizeExecution(completed: Boolean): Unit = {
    if (running) {
      if (!completed) {
        pollingThread.interrupt();
        startedProcesses.filter(x => isProcessCompleted(x._1)).map(_._2).foreach(_.stop());
      }

      runner.removeListener(listener);
      running = false;
    }
  }
}