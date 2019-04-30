package cn.piflow

import java.sql.Date
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.{CountDownLatch, TimeUnit}

import scala.collection.mutable.{ArrayBuffer, Map => MMap}
import cn.piflow.Execution
import cn.piflow.util.PropertyUtil
import cn.piflow.util.PropertyUtil
import org.apache.spark.launcher.SparkAppHandle.State
import org.apache.spark.launcher.{SparkAppHandle, SparkLauncher}
import org.apache.spark.sql.SparkSession

/**
  * Created by bluejoe on 2018/6/27.
  */


trait FlowGroup extends ProjectEntry{

  def addFlow(name: String, flow: Flow, con: Condition[FlowGroupExecution] = Condition.AlwaysTrue[FlowGroupExecution]);

  def mapFlowWithConditions(): Map[String, (Flow, Condition[FlowGroupExecution])];

  def getFlowGroupName(): String;

  def setFlowGroupName(flowGroupName : String): Unit;
}


class FlowGroupImpl extends FlowGroup {

  var name = ""
  var uuid = ""

  val _mapFlowWithConditions = MMap[String, (Flow, Condition[FlowGroupExecution])]();

  def addFlow(name: String, flow: Flow, con: Condition[FlowGroupExecution] = Condition.AlwaysTrue[FlowGroupExecution]) = {
    _mapFlowWithConditions(name) = flow -> con;
  }

  def mapFlowWithConditions(): Map[String, (Flow, Condition[FlowGroupExecution])] = _mapFlowWithConditions.toMap;

  override def getFlowGroupName(): String = {
    this.name
  }

  override def setFlowGroupName(flowGroupName: String): Unit = {
    this.name = flowGroupName
  }
}

trait FlowGroupExecution extends Execution{

  def isFlowGroupCompleted() : Boolean;

  def stop(): Unit;

  def awaitTermination(): Unit;

  def awaitTermination(timeout: Long, unit: TimeUnit): Unit;

}

/*class FlowGroupExecutionImpl(fg: FlowGroup, runnerContext: Context, runner: Runner) extends FlowGroupExecution {
  val flowGroupContext = createContext(runnerContext);
  val flowGroupExecution = this;

  val mapFlowWithConditions: Map[String, (Flow, Condition[FlowGroupExecution])] = fg.mapFlowWithConditions();
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

    override def onFlowGroupStarted(ctx: FlowGroupContext): Unit = {

    }

    override def onFlowGroupCompleted(ctx: FlowGroupContext): Unit = {

    }

    override def onFlowGroupFailed(ctx: FlowGroupContext): Unit = {

    }
  };
  runner.addListener(listener);
  val runnerListener = runner.getListener()


  def isFlowGroupCompleted(): Boolean = {
    completedProcesses.foreach( en =>{
      if(en._2 == false){
        return false
      }
    })
    return true
  }

  private def startProcess(name: String, flow: Flow): Unit = {

    //TODO
    val process = runner.start(flow);
    startedProcesses(name) = process;
  }

  val pollingThread = new Thread(new Runnable() {
    override def run(): Unit = {

      runnerListener.onFlowGroupStarted(flowGroupContext)

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

      runnerListener.onFlowGroupCompleted(flowGroupContext)
      //TODO: how to define FlowGroup Failed
      //runnerListener.onFlowGroupFailed(ctx)
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
      }

      runner.removeListener(listener);
      running = false;
    }
  }

  private def createContext(runnerContext: Context): FlowGroupContext = {
    new CascadeContext(runnerContext) with FlowGroupContext {
      override def getFlowGroup(): FlowGroup = fg

      override def getFlowGroupExecution(): FlowGroupExecution = flowGroupExecution
    };
  }

  override def isEntryCompleted(name: String): Boolean = {
    completedProcesses(name);
  }
}*/

class FlowGroupExecutionImpl(fg: FlowGroup, runnerContext: Context, runner: Runner) extends FlowGroupExecution {
  val flowGroupContext = createContext(runnerContext);
  val flowGroupExecution = this;

  val mapFlowWithConditions: Map[String, (Flow, Condition[FlowGroupExecution])] = fg.mapFlowWithConditions();
  val completedProcesses = MMap[String, Boolean]();
  completedProcesses ++= mapFlowWithConditions.map(x => (x._1, false));
  val numWaitingProcesses = new AtomicInteger(mapFlowWithConditions.size);

  val startedProcesses = MMap[String, SparkAppHandle]();

  val execution = this;
  val POLLING_INTERVAL = 1000;
  val latch = new CountDownLatch(1);
  var running = true;


  val runnerListener = runner.getListener()


  def isFlowGroupCompleted(): Boolean = {
    completedProcesses.foreach( en =>{
      if(en._2 == false){
        return false
      }
    })
    return true
  }

  private def startProcess(name: String, flow: Flow): Unit = {

    println(flow.getFlowJson())

    var flowJson = flow.getFlowJson()
    flowJson = flowJson.replaceAll("}","}\n")
    //TODO
    var appId : String = ""
    val countDownLatch = new CountDownLatch(1)
    val launcher = new SparkLauncher
    val handle =launcher
      .setAppName(flow.getFlowName())
      .setMaster(PropertyUtil.getPropertyValue("spark.master"))
      .setDeployMode(PropertyUtil.getPropertyValue("spark.deploy.mode"))
      .setAppResource(PropertyUtil.getPropertyValue("piflow.bundle"))
      .setVerbose(true)
      .setConf("spark.hadoop.yarn.resourcemanager.hostname", PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname"))
      .setConf("spark.hadoop.yarn.resourcemanager.address", PropertyUtil.getPropertyValue("yarn.resourcemanager.address"))
      .setConf("spark.yarn.access.namenode", PropertyUtil.getPropertyValue("yarn.access.namenode"))
      .setConf("spark.yarn.stagingDir", PropertyUtil.getPropertyValue("yarn.stagingDir"))
      .setConf("spark.yarn.jars", PropertyUtil.getPropertyValue("yarn.jars"))
      .setConf("spark.jars", PropertyUtil.getPropertyValue("piflow.bundle"))
      .setConf("spark.hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .setConf("spark.driver.memory", flow.getDriverMemory())
      .setConf("spark.num.executors", flow.getExecutorNum())
      .setConf("spark.executor.memory", flow.getExecutorMem())
      .setConf("spark.executor.cores",flow.getExecutorCores())
      .addFile(PropertyUtil.getConfigureFile())
      .setMainClass("cn.piflow.api.StartFlowMain")
      .addAppArgs(flowJson)
      .startApplication( new SparkAppHandle.Listener {
      override def stateChanged(handle: SparkAppHandle): Unit = {
        appId = handle.getAppId
        val sparkAppState = handle.getState
        if(appId != null){
          println("Spark job with app id: " + appId + ",\t State changed to: " + sparkAppState)
        }else{
          println("Spark job's state changed to: " + sparkAppState)
        }

        //TODO: get the process status
        if (handle.getState.equals(State.FINISHED)){
          completedProcesses(flow.getFlowName()) = true;
          numWaitingProcesses.decrementAndGet();
        }
        if (handle.getState().isFinal){
          countDownLatch.countDown()
          println("Task is finished!")
        }
      }
      override def infoChanged(handle: SparkAppHandle): Unit = {

      }
    }
    )

    startedProcesses(name) = handle;
  }

  val pollingThread = new Thread(new Runnable() {
    override def run(): Unit = {

      runnerListener.onFlowGroupStarted(flowGroupContext)

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

      runnerListener.onFlowGroupCompleted(flowGroupContext)
      //TODO: how to define FlowGroup Failed
      //runnerListener.onFlowGroupFailed(ctx)
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
      }

      running = false;
    }
  }

  private def createContext(runnerContext: Context): FlowGroupContext = {
    new CascadeContext(runnerContext) with FlowGroupContext {
      override def getFlowGroup(): FlowGroup = fg

      override def getFlowGroupExecution(): FlowGroupExecution = flowGroupExecution
    };
  }

  override def isEntryCompleted(name: String): Boolean = {
    completedProcesses(name);
  }
}
