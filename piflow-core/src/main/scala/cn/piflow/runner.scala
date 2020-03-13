package cn.piflow

import java.util.Date

import cn.piflow.util._
import org.apache.spark.sql.SparkSession

import scala.collection.mutable.ArrayBuffer

trait Runner {
  def bind(key: String, value: Any): Runner;

  def start(flow: Flow): Process;

  def start(group: Group): GroupExecution;

  def addListener(listener: RunnerListener);

  def removeListener(listener: RunnerListener);

  def getListener(): RunnerListener;
}

object Runner {
  def create(): Runner = new Runner() {
    val listeners = ArrayBuffer[RunnerListener](new RunnerLogger());

    val compositeListener = new RunnerListener() {
      override def onProcessStarted(ctx: ProcessContext): Unit = {
        listeners.foreach(_.onProcessStarted(ctx));
      }

      override def onProcessFailed(ctx: ProcessContext): Unit = {
        listeners.foreach(_.onProcessFailed(ctx));
      }

      override def onProcessCompleted(ctx: ProcessContext): Unit = {
        listeners.foreach(_.onProcessCompleted(ctx));
      }

      override def onJobStarted(ctx: JobContext): Unit = {
        listeners.foreach(_.onJobStarted(ctx));
      }

      override def onJobCompleted(ctx: JobContext): Unit = {
        listeners.foreach(_.onJobCompleted(ctx));
      }

      override def onJobInitialized(ctx: JobContext): Unit = {
        listeners.foreach(_.onJobInitialized(ctx));
      }

      override def onProcessForked(ctx: ProcessContext, child: ProcessContext): Unit = {
        listeners.foreach(_.onProcessForked(ctx, child));
      }

      override def onJobFailed(ctx: JobContext): Unit = {
        listeners.foreach(_.onJobFailed(ctx));
      }

      override def onProcessAborted(ctx: ProcessContext): Unit = {
        listeners.foreach(_.onProcessAborted(ctx));
      }

      override def monitorJobCompleted(ctx: JobContext, outputs: JobOutputStream): Unit = {
        //TODO:
        listeners.foreach(_.monitorJobCompleted(ctx, outputs));
      }

      override def onGroupStarted(ctx: GroupContext): Unit = {
        listeners.foreach(_.onGroupStarted(ctx));
      }

      override def onGroupCompleted(ctx: GroupContext): Unit = {
        listeners.foreach(_.onGroupCompleted(ctx));
      }

      override def onGroupFailed(ctx: GroupContext): Unit = {
        listeners.foreach(_.onGroupFailed(ctx));
      }

      override def onGroupStoped(ctx: GroupContext): Unit = {
        //TODO
      }
    }

    override def addListener(listener: RunnerListener) = {
      listeners += listener;
    }

    override def getListener(): RunnerListener = compositeListener;

    val ctx = new CascadeContext();

    override def bind(key: String, value: Any): this.type = {
      ctx.put(key, value);
      this;
    }

    override def start(flow: Flow): Process = {
      new ProcessImpl(flow, ctx, this);
    }

    override def start(group: Group): GroupExecution = {
      new GroupExecutionImpl(group, ctx, this);
    }

    override def removeListener(listener: RunnerListener): Unit = {
      listeners -= listener;
    }
  }
}

trait RunnerListener {
  def onProcessStarted(ctx: ProcessContext);

  def onProcessForked(ctx: ProcessContext, child: ProcessContext);

  def onProcessCompleted(ctx: ProcessContext);

  def onProcessFailed(ctx: ProcessContext);

  def onProcessAborted(ctx: ProcessContext);

  def onJobInitialized(ctx: JobContext);

  def onJobStarted(ctx: JobContext);

  def onJobCompleted(ctx: JobContext);

  def onJobFailed(ctx: JobContext);

  def monitorJobCompleted(ctx: JobContext,outputs : JobOutputStream);

  def onGroupStarted(ctx: GroupContext);

  def onGroupCompleted(ctx: GroupContext);

  def onGroupFailed(ctx: GroupContext);

  def onGroupStoped(ctx: GroupContext);

}


class RunnerLogger extends RunnerListener with Logging {
  //TODO: add GroupID or ProjectID
  override def onProcessStarted(ctx: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    val flowName = ctx.getFlow().toString;
    val time = new Date().toString
    logger.debug(s"process started: $pid, flow: $flowName, time: $time");
    println(s"process started: $pid, flow: $flowName, time: $time")
    //update flow state to STARTED
    val appId = getAppId(ctx)
    H2Util.addFlow(appId,pid,ctx.getFlow().getFlowName())
    H2Util.updateFlowState(appId,FlowState.STARTED)
    H2Util.updateFlowStartTime(appId,time)
  };

  override def onJobStarted(ctx: JobContext): Unit = {
    val jid = ctx.getStopJob().jid();
    val stopName = ctx.getStopJob().getStopName();
    val time = new Date().toString
    logger.debug(s"job started: $jid, stop: $stopName, time: $time");
    println(s"job started: $jid, stop: $stopName, time: $time")
    //update stop state to STARTED
    H2Util.updateStopState(getAppId(ctx),stopName,StopState.STARTED)
    H2Util.updateStopStartTime(getAppId(ctx),stopName,time)
  };

  override def onJobFailed(ctx: JobContext): Unit = {
    ctx.getProcessContext()
    val stopName = ctx.getStopJob().getStopName();
    val time = new Date().toString
    logger.debug(s"job failed: $stopName, time: $time");
    println(s"job failed: $stopName, time: $time")
    //update stop state to FAILED
    H2Util.updateStopState(getAppId(ctx),stopName,StopState.FAILED)
    H2Util.updateStopFinishedTime(getAppId(ctx),stopName,time)
  };

  override def onJobInitialized(ctx: JobContext): Unit = {
    val stopName = ctx.getStopJob().getStopName();
    val time = new Date().toString
    logger.debug(s"job initialized: $stopName, time: $time");
    println(s"job initialized: $stopName, time: $time")
    //add stop into h2 db and update stop state to INIT
    val appId = getAppId(ctx)
    H2Util.addStop(appId,stopName)
    H2Util.updateStopState(appId,stopName,StopState.INIT)
  };

  override def onProcessCompleted(ctx: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    val time = new Date().toString
    logger.debug(s"process completed: $pid, time: $time");
    println(s"process completed: $pid, time: $time")
    //update flow state to COMPLETED
    val appId = getAppId(ctx)
    H2Util.updateFlowState(appId,FlowState.COMPLETED)
    H2Util.updateFlowFinishedTime(appId,time)
  };

  override def onJobCompleted(ctx: JobContext): Unit = {
    val stopName = ctx.getStopJob().getStopName();
    val time = new Date().toString
    logger.debug(s"job completed: $stopName, time: $time");
    println(s"job completed: $stopName, time: $time")
    //update stop state to COMPLETED
    val appId = getAppId(ctx)
    H2Util.updateStopState(appId,stopName,StopState.COMPLETED)
    H2Util.updateStopFinishedTime(appId,stopName,time)
  };

  override def onProcessFailed(ctx: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    val time = new Date().toString
    logger.debug(s"process failed: $pid, time: $time");
    println(s"process failed: $pid, time: $time")
    //update flow state to FAILED
    val appId = getAppId(ctx)
    H2Util.updateFlowState(getAppId(ctx),FlowState.FAILED)
    H2Util.updateFlowFinishedTime(appId,time)
  }

  override def onProcessAborted(ctx: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    val time = new Date().toString
    logger.debug(s"process aborted: $pid, time: $time");
    println(s"process aborted: $pid, time: $time")
    //update flow state to ABORTED
    val appId = getAppId(ctx)
    H2Util.updateFlowState(appId,FlowState.ABORTED)
    H2Util.updateFlowFinishedTime(appId,time)
  }

  override def onProcessForked(ctx: ProcessContext, child: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    val cid = child.getProcess().pid();
    val time = new Date().toString
    logger.debug(s"process forked: $pid, child flow execution: $cid, time: $time");
    println(s"process forked: $pid, child flow execution: $cid, time: $time")
    //update flow state to FORK
    H2Util.updateFlowState(getAppId(ctx),FlowState.FORK)
  }

  private def getAppId(ctx: Context) : String = {
    val sparkSession = ctx.get(classOf[SparkSession].getName).asInstanceOf[SparkSession]
    sparkSession.sparkContext.applicationId
  }

  override def monitorJobCompleted(ctx: JobContext, outputs: JobOutputStream): Unit = {
    val appId = getAppId(ctx)
    val stopName = ctx.getStopJob().getStopName();
    logger.debug(s"job completed: monitor $stopName");
    println(s"job completed: monitor $stopName")

    val outputDataCount = outputs.getDataCount()
    outputDataCount.keySet.foreach(portName => {
      H2Util.addThroughput(appId, stopName, portName, outputDataCount(portName))
    })
  }

  override def onGroupStarted(ctx: GroupContext): Unit = {
    //TODO: write monitor data into db
    val groupId = ctx.getGroupExecution().getGroupId()
    val flowGroupName = ctx.getGroup().getGroupName()
    val childCount = ctx.getGroupExecution().getChildCount()
    val time = new Date().toString
    //val flowCount = ctx.getGroupExecution().getFlowCount();
    logger.debug(s"Group started: $groupId, group: $flowGroupName, time: $time");
    println(s"Group started: $groupId, group: $flowGroupName, time: $time")
    //update flow group state to STARTED
    H2Util.addGroup(groupId, flowGroupName, childCount)
    H2Util.updateGroupState(groupId,GroupState.STARTED)
    H2Util.updateGroupStartTime(groupId,time)
  }

  override def onGroupCompleted(ctx: GroupContext): Unit = {
    //TODO: write monitor data into db
    val groupId = ctx.getGroupExecution().getGroupId()
    val flowGroupName = ctx.getGroup().getGroupName()
    val time = new Date().toString
    logger.debug(s"Group completed: $groupId, time: $time");
    println(s"Group completed: $groupId, time: $time")
    //update flow group state to COMPLETED
    H2Util.updateGroupState(groupId,GroupState.COMPLETED)
    H2Util.updateGroupFinishedTime(groupId,time)
  }

  override def onGroupStoped(ctx: GroupContext): Unit = {
    //TODO: write monitor data into db
    val groupId = ctx.getGroupExecution().getGroupId()
    val flowGroupName = ctx.getGroup().getGroupName()
    val time = new Date().toString
    logger.debug(s"Group stoped: $groupId, time: $time");
    println(s"Group stoped: $groupId, time: $time")
    //update flow group state to COMPLETED
    H2Util.updateGroupState(groupId,GroupState.KILLED)
    H2Util.updateGroupFinishedTime(groupId,time)

  }

  override def onGroupFailed(ctx: GroupContext): Unit = {
    //TODO: write monitor data into db
    val groupId = ctx.getGroupExecution().getGroupId()
    val flowGroupName = ctx.getGroup().getGroupName()
    val time = new Date().toString
    logger.debug(s"Group failed: $groupId, time: $time");
    println(s"Group failed: $groupId, time: $time")
    //update flow group state to FAILED
    H2Util.updateGroupState(groupId,GroupState.FAILED)
    H2Util.updateGroupFinishedTime(groupId,time)
  }

}
