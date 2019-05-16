package cn.piflow

import java.util.Date
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.{CountDownLatch, TimeUnit}

import cn.piflow.util._
import org.apache.spark.launcher.{SparkAppHandle, SparkLauncher}
import org.apache.spark.launcher.SparkAppHandle.State

import scala.collection.mutable.{ArrayBuffer, Map => MMap}


/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */

trait Project {
  def addProjectEntry(name: String, flowOrGroup: ProjectEntry, con: Condition[ProjectExecution] = Condition.AlwaysTrue[ProjectExecution]);

  def mapFlowWithConditions(): Map[String, (ProjectEntry, Condition[ProjectExecution])];

  def getProjectName(): String;

  def setProjectName(projectName : String): Unit;
}


class ProjectImpl extends Project {
  var name = ""
  var uuid = ""

  val _mapFlowWithConditions = MMap[String, (ProjectEntry, Condition[ProjectExecution])]();

  def addProjectEntry(name: String, flowOrGroup: ProjectEntry, con: Condition[ProjectExecution] = Condition.AlwaysTrue[ProjectExecution]) = {
    _mapFlowWithConditions(name) = flowOrGroup -> con;
  }

  def mapFlowWithConditions(): Map[String, (ProjectEntry, Condition[ProjectExecution])] = _mapFlowWithConditions.toMap;

  override def getProjectName(): String = {
    this.name
  }

  override def setProjectName(projectName: String): Unit = {
    this.name = projectName
  }
}

trait ProjectExecution extends Execution{

  def stop(): Unit;

  def awaitTermination(): Unit;

  def awaitTermination(timeout: Long, unit: TimeUnit): Unit;

  def projectId() : String;
}

class ProjectExecutionImpl(project: Project, runnerContext: Context, runner: Runner) extends ProjectExecution {

  val projectContext = createContext(runnerContext);
  val projectExecution = this;

  val id : String = "project_" + IdGenerator.uuid();

  val mapProjectEntryWithConditions: Map[String, (ProjectEntry, Condition[ProjectExecution])] = project.mapFlowWithConditions();
  val completedProjectEntry = MMap[String, Boolean]();
  completedProjectEntry ++= mapProjectEntryWithConditions.map(x => (x._1, false));
  val numWaitingProjectEntry = new AtomicInteger(mapProjectEntryWithConditions.size);

  val startedProcesses = MMap[String, SparkAppHandle]();
  val startedFlowGroup = MMap[String, FlowGroupExecution]()

  val startedProcessesAppID = MMap[String, String]()

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
        completedProjectEntry(x._1) = true;
        numWaitingProjectEntry.decrementAndGet();
      }
    }

    override def onFlowGroupFailed(ctx: FlowGroupContext): Unit = {}

    override def onProjectStarted(ctx: ProjectContext): Unit = {}

    override def onProjectCompleted(ctx: ProjectContext): Unit = {}

    override def onProjectFailed(ctx: ProjectContext): Unit = {}

    override def onFlowGroupStoped(ctx: FlowGroupContext): Unit = {}

    override def onProjectStoped(ctx: ProjectContext): Unit = {}
  };

  runner.addListener(listener);
  val runnerListener = runner.getListener()


  def isEntryCompleted(name: String): Boolean = {
    completedProjectEntry(name)
  }

  private def startProcess(name: String, flow: Flow, projectId: String = ""): Unit = {

    println(flow.getFlowJson())

    var flowJson = flow.getFlowJson()
    flowJson = flowJson.replaceAll("}","}\n")

    var appId : String = ""
    val countDownLatch = new CountDownLatch(1)

    val handle = FlowLauncher.launch(flow).startApplication( new SparkAppHandle.Listener {
      override def stateChanged(handle: SparkAppHandle): Unit = {
        appId = handle.getAppId
        val sparkAppState = handle.getState
        if(appId != null){
          println("Spark job with app id: " + appId + ",\t State changed to: " + sparkAppState)
        }else{
          println("Spark job's state changed to: " + sparkAppState)
        }
        if(!H2Util.getFlowProcessId(appId).equals("")){
          //H2Util.updateFlowGroupId(appId,groupId)
        }

        if(H2Util.getFlowState(appId).equals(FlowState.COMPLETED)){
          completedProjectEntry(flow.getFlowName()) = true;
          numWaitingProjectEntry.decrementAndGet();
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


    while (handle.getAppId ==  null){

      Thread.sleep(100)
    }
    appId = handle.getAppId

    //wait flow process started
    while(H2Util.getFlowProcessId(appId).equals("")){
      Thread.sleep(1000)
    }

    if(projectId != ""){
      H2Util.updateFlowProjectId(appId, projectId)
    }

    startedProcesses(name) = handle;
    startedProcessesAppID(name) = appId
  }

  private def startFlowGroup(name: String, flowGroup: FlowGroup, projectId: String): Unit = {
    val flowGroupExecution = runner.start(flowGroup);
    startedFlowGroup(name) = flowGroupExecution;
    val flowGroupId = flowGroupExecution.groupId()
    while(H2Util.getFlowGroupState(flowGroupId).equals("")){
      Thread.sleep(1000)
    }
    if(projectId != ""){
      H2Util.updateFlowGroupProject(flowGroupId,projectId)
    }
  }

  val pollingThread = new Thread(new Runnable() {
    override def run(): Unit = {

      runnerListener.onProjectStarted(projectContext)

      try{
        while (numWaitingProjectEntry.get() > 0) {
          val todosFlow = ArrayBuffer[(String, Flow)]();
          val todosFlowGroup = ArrayBuffer[(String, FlowGroup)]();
          mapProjectEntryWithConditions.foreach { en =>

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
            todosFlow.foreach(en => startProcess(en._1, en._2.asInstanceOf[Flow],id));
          }
          startedFlowGroup.synchronized{
            todosFlowGroup.foreach(en => startFlowGroup(en._1, en._2.asInstanceOf[FlowGroup],id))
          }

          Thread.sleep(POLLING_INTERVAL);
        }

        runnerListener.onProjectCompleted(projectContext)

      }catch {
        case e: Throwable =>
          runnerListener.onProjectFailed(projectContext);
          throw e;
      }
      finally {
        latch.countDown();
        finalizeExecution(true);
      }
    }
  });

  pollingThread.start();

  override def awaitTermination(): Unit = {
    latch.await();
    finalizeExecution(true);
  }

  override def stop(): Unit = {
    finalizeExecution(false);
    //runnerListener.onProjectStoped(projectContext)
  }

  override def awaitTermination(timeout: Long, unit: TimeUnit): Unit = {
    if (!latch.await(timeout, unit))
      finalizeExecution(false);
  }

  private def finalizeExecution(completed: Boolean): Unit = {
    if (running) {
      if (!completed) {
        //pollingThread.interrupt();
        //startedProcesses.filter(x => !isEntryCompleted(x._1)).map(_._2).foreach(_.stop());
        startedProcesses.synchronized{
          startedProcesses.filter(x => !isEntryCompleted(x._1)).foreach(x => {

            x._2.stop()
            val appID: String = startedProcessesAppID.getOrElse(x._1,"")
            if(!appID.equals("")){
              println("Stop Flow " + appID + " by FlowLauncher!")
              FlowLauncher.stop(appID)
            }

          });
        }
        startedFlowGroup.synchronized{
          startedFlowGroup.filter(x => !isEntryCompleted(x._1)).map(_._2).foreach(_.stop());
        }

        pollingThread.interrupt();

      }

      runner.removeListener(listener);
      running = false;
    }
  }

  private def createContext(runnerContext: Context): ProjectContext = {
    new CascadeContext(runnerContext) with ProjectContext {
      override def getProject(): Project = project

      override def getProjectExecution(): ProjectExecution = projectExecution
    };
  }

  override def projectId(): String = id
}