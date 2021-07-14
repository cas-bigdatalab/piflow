package cn.piflow

import java.lang.Thread.UncaughtExceptionHandler
import java.util.Date
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.{CountDownLatch, TimeUnit}

import cn.piflow.util._
import org.apache.spark.launcher.{SparkAppHandle, SparkLauncher}

import scala.collection.mutable.{ArrayBuffer, Map => MMap}
import scala.util.{Failure, Success, Try}


/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */

trait Group extends GroupEntry{
  def addGroupEntry(name: String, flowOrGroup: GroupEntry, con: Condition[GroupExecution] = Condition.AlwaysTrue[GroupExecution]);

  def mapFlowWithConditions(): Map[String, (GroupEntry, Condition[GroupExecution])];

  def mapContitions : MMap[String, DataCenterConditionBean];

  def getGroupName(): String;

  def setGroupName(groupName : String): Unit;

  def getParentGroupId():String;

  def setParentGroupId( groupId : String) : Unit;

}


class GroupImpl extends Group {
  var name = ""
  var uuid = ""
  var parentId = ""

  val _mapFlowWithConditions = MMap[String, (GroupEntry, Condition[GroupExecution])]();

  def addGroupEntry(name: String, flowOrGroup: GroupEntry, con: Condition[GroupExecution] = Condition.AlwaysTrue[GroupExecution]) = {
    _mapFlowWithConditions(name) = flowOrGroup -> con;
  }

  def mapFlowWithConditions(): Map[String, (GroupEntry, Condition[GroupExecution])] = _mapFlowWithConditions.toMap;

  override def getGroupName(): String = {
    this.name
  }

  override def setGroupName(groupName: String): Unit = {
    this.name = groupName
  }

  override def getParentGroupId(): String = {
    this.parentId
  }

  override def setParentGroupId(groupId: String): Unit = {
    this.parentId = groupId
  }

  override def mapContitions: MMap[String, DataCenterConditionBean] = {null}
}

trait GroupExecution extends Execution{

  def stop(): Unit;

  def awaitTermination(): Unit;

  def awaitTermination(timeout: Long, unit: TimeUnit): Unit;

  def getGroupId() : String;

  def getChildCount() : Int;
}

class GroupExecutionImpl(group: Group, runnerContext: Context, runner: Runner) extends GroupExecution {

  val groupContext = createContext(runnerContext);
  val groupExecution = this;

  val id : String = "group_" + IdGenerator.uuid();

  val mapGroupEntryWithConditions: Map[String, (GroupEntry, Condition[GroupExecution])] = group.mapFlowWithConditions();
  val completedGroupEntry = MMap[String, Boolean]();
  completedGroupEntry ++= mapGroupEntryWithConditions.map(x => (x._1, false))
  val numWaitingGroupEntry = new AtomicInteger(mapGroupEntryWithConditions.size)

  val startedProcesses = MMap[String, SparkAppHandle]();
  val startedGroup = MMap[String, GroupExecution]()

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

    override def onGroupStarted(ctx: GroupContext): Unit = {}

    override def onGroupCompleted(ctx: GroupContext): Unit = {
      startedGroup.filter(_._2 == ctx.getGroupExecution()).foreach { x =>
        completedGroupEntry(x._1) = true;
        numWaitingGroupEntry.decrementAndGet();
      }
    }

    override def onGroupStoped(ctx: GroupContext): Unit = {}

    override def onGroupFailed(ctx: GroupContext): Unit = {}
  };

  runner.addListener(listener);
  val runnerListener = runner.getListener()


  def isEntryCompleted(name: String): Boolean = {
    completedGroupEntry(name)
  }

  private def startProcess(name: String, flow: Flow, groupId: String = ""): Unit = {

    println(flow.getFlowJson())

    var flowJson = flow.getFlowJson()

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
          completedGroupEntry(flow.getFlowName()) = true;
          numWaitingGroupEntry.decrementAndGet();
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

    if(groupId != ""){
      H2Util.updateFlowGroupId(appId, groupId)
    }

    startedProcesses(name) = handle
    startedProcessesAppID(name) = appId
   }

  private def startGroup(name: String, group: Group, parentId: String): Unit = {
    val groupExecution = runner.start(group);
    startedGroup(name) = groupExecution;
    val groupId = groupExecution.getGroupId()
    while(H2Util.getGroupState(groupId).equals("")){
      Thread.sleep(1000)
    }
    if(parentId != ""){
      H2Util.updateGroupParent(groupId,parentId)
    }
  }


  @volatile
  var maybeException:Option[Throwable] = None
  val pollingThread = new Thread(new Runnable() {
    override def run(): Unit = {

      runnerListener.onGroupStarted(groupContext)

      try{
        while (numWaitingGroupEntry.get() > 0) {

          val (todosFlow, todosGroup) = getTodos()

          if(todosFlow.size == 0 && todosGroup.size == 0 &&  H2Util.isGroupChildError(id) && !H2Util.isGroupChildRunning(id)){
            val (todosFlow, todosGroup) = getTodos()
            if(todosFlow.size == 0 && todosGroup.size == 0)
              throw new GroupException("Group Failed!")

          }

          startedProcesses.synchronized {
            todosFlow.foreach(en => {
              startProcess(en._1, en._2.asInstanceOf[Flow],id)
            });
          }
          startedGroup.synchronized{
            todosGroup.foreach(en => {
              startGroup(en._1, en._2.asInstanceOf[Group],id)
            })
          }

          Thread.sleep(POLLING_INTERVAL);
        }

        runnerListener.onGroupCompleted(groupContext)

      }catch {
        case e: Throwable =>
          runnerListener.onGroupFailed(groupContext);
          println(e)
          if(e.isInstanceOf[GroupException])
            throw e
      }
      finally {
        latch.countDown();
        finalizeExecution(true);
      }
    }
  });

  val doit = Try{
    pollingThread.setUncaughtExceptionHandler( new UncaughtExceptionHandler {
      override def uncaughtException(thread: Thread, throwable: Throwable): Unit = {
        maybeException = Some(throwable)
      }
    })
    pollingThread.start()
    //pollingThread.join()
  }

  doit match {
    case Success(v) => {
      println("Did not capture error!")
    }
    case Failure(v) =>{
      println("Capture error!")
      runnerListener.onGroupFailed(groupContext)
    }

  }

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
        startedGroup.synchronized{
          startedGroup.filter(x => !isEntryCompleted(x._1)).map(_._2).foreach(_.stop());
        }

        pollingThread.interrupt();

      }

      runner.removeListener(listener);
      running = false;
    }
  }

  private def createContext(runnerContext: Context): GroupContext = {
    new CascadeContext(runnerContext) with GroupContext {
      override def getGroup(): Group = group

      override def getGroupExecution(): GroupExecution = groupExecution

    };
  }

  private def getTodos() : (ArrayBuffer[(String, Flow)], ArrayBuffer[(String, Group)]) = {

    val todosFlow = ArrayBuffer[(String, Flow)]();
    val todosGroup = ArrayBuffer[(String, Group)]();
    mapGroupEntryWithConditions.foreach { en =>
      if(en._2._1.isInstanceOf[Flow]){
        if (!startedProcesses.contains(en._1) && en._2._2.matches(execution)) {
          todosFlow += (en._1 -> en._2._1.asInstanceOf[Flow]);
        }
      }else if (en._2._1.isInstanceOf[Group]){
        if (!startedGroup.contains(en._1) && en._2._2.matches(execution)) {
          todosGroup += (en._1 -> en._2._1.asInstanceOf[Group]);
        }
      }

    }
    (todosFlow, todosGroup)
  }

  override def getGroupId(): String = id

  override def getChildCount(): Int = {
    mapGroupEntryWithConditions.size

  }
}