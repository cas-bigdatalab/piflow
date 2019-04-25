package cn.piflow

import java.sql.Date
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.{CountDownLatch, TimeUnit}

import scala.collection.mutable.{ArrayBuffer, Map => MMap}


/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */

trait Project {
  def addProjectEntry(name: String, flowOrGroup: ProjectEntry, con: Condition[ProjectExecution] = Condition.AlwaysTrue[ProjectExecution]);

  def mapFlowWithConditions(): Map[String, (ProjectEntry, Condition[ProjectExecution])];
}


class ProjectImpl extends Project {
  val _mapFlowWithConditions = MMap[String, (ProjectEntry, Condition[ProjectExecution])]();

  def addProjectEntry(name: String, flowOrGroup: ProjectEntry, con: Condition[ProjectExecution] = Condition.AlwaysTrue[ProjectExecution]) = {
    _mapFlowWithConditions(name) = flowOrGroup -> con;
  }

  def mapFlowWithConditions(): Map[String, (ProjectEntry, Condition[ProjectExecution])] = _mapFlowWithConditions.toMap;
}

trait ProjectExecution extends Execution{

  def stop(): Unit;

  def awaitTermination(): Unit;

  def awaitTermination(timeout: Long, unit: TimeUnit): Unit;
}

class ProjectExecutionImpl(project: Project, runnerContext: Context, runner: Runner) extends ProjectExecution {
  val mapFlowWithConditions: Map[String, (ProjectEntry, Condition[ProjectExecution])] = project.mapFlowWithConditions();
  val completedProcesses = MMap[String, Boolean]();
  completedProcesses ++= mapFlowWithConditions.map(x => (x._1, false));
  val numWaitingProcesses = new AtomicInteger(mapFlowWithConditions.size);

  val startedProcesses = MMap[String, Process]();
  val startedFlowGroup = MMap[String, FlowGroupExecution]()

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

    override def onFlowGroupStarted(ctx: FlowGroupContext): Unit = {}

    override def onFlowGroupCompleted(ctx: FlowGroupContext): Unit = {
      startedFlowGroup.filter(_._2 == ctx.getFlowGroupExecution()).foreach { x =>
        completedProcesses(x._1) = true;
        numWaitingProcesses.decrementAndGet();
      }
    }

    override def onFlowGroupFailed(ctx: FlowGroupContext): Unit = {}
  };

  runner.addListener(listener);


  def isEntryCompleted(name: String): Boolean = {
    completedProcesses(name)
  }

  private def startProcess(name: String, flow: Flow): Unit = {
    val process = runner.start(flow);
    startedProcesses(name) = process;
  }

  private def startFlowGroup(name: String, flowGroup: FlowGroup): Unit = {
    val flowGroupExecution = runner.start(flowGroup);
    startedFlowGroup(name) = flowGroupExecution;
  }

  val pollingThread = new Thread(new Runnable() {
    override def run(): Unit = {
      while (numWaitingProcesses.get() > 0) {
        val todosFlow = ArrayBuffer[(String, Flow)]();
        val todosFlowGroup = ArrayBuffer[(String, FlowGroup)]();
        mapFlowWithConditions.foreach { en =>

          if(en._2._1.isInstanceOf[Flow]){
            if (!startedProcesses.contains(en._1) && en._2._2.matches(execution)) {
              todosFlow += (en._1 -> en._2._1.asInstanceOf[Flow]);
            }
          }else if (en._2._1.isInstanceOf[FlowGroup]){
            if (!startedFlowGroup.contains(en._1) && en._2._2.matches(execution)) {
              todosFlowGroup += (en._1 -> en._2._1.asInstanceOf[FlowGroup]);
            }
          }

        }

        startedProcesses.synchronized {
          todosFlow.foreach(en => startProcess(en._1, en._2.asInstanceOf[Flow]));
        }
        startedFlowGroup.synchronized{
          todosFlowGroup.foreach(en => startFlowGroup(en._1, en._2.asInstanceOf[FlowGroup]))
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
        startedProcesses.filter(x => isEntryCompleted(x._1)).map(_._2).foreach(_.stop());
        startedFlowGroup.filter(x => isEntryCompleted(x._1)).map(_._2).foreach(_.stop());
      }

      runner.removeListener(listener);
      running = false;
    }
  }
}