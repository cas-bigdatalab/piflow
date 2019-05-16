package cn.piflow

import java.util.Date

import cn.piflow.util._
import org.apache.spark.sql.SparkSession

import scala.collection.mutable.ArrayBuffer

trait Runner {
  def bind(key: String, value: Any): Runner;

  def start(flow: Flow): Process;

  def start(flowGroup: FlowGroup): FlowGroupExecution;

  def start(project: Project): ProjectExecution;

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

      override def onFlowGroupStarted(ctx: FlowGroupContext): Unit = {
        listeners.foreach(_.onFlowGroupStarted(ctx));
      }

      override def onFlowGroupCompleted(ctx: FlowGroupContext): Unit = {
        listeners.foreach(_.onFlowGroupCompleted(ctx));
      }

      override def onFlowGroupFailed(ctx: FlowGroupContext): Unit = {
        listeners.foreach(_.onFlowGroupFailed(ctx));
      }

      override def onProjectStarted(ctx: ProjectContext): Unit = {
        listeners.foreach(_.onProjectStarted(ctx));
      }

      override def onProjectCompleted(ctx: ProjectContext): Unit = {
        listeners.foreach(_.onProjectCompleted(ctx));
      }

      override def onProjectFailed(ctx: ProjectContext): Unit = {
        listeners.foreach(_.onProjectFailed(ctx));
      }

      override def onFlowGroupStoped(ctx: FlowGroupContext): Unit = {
        listeners.foreach(_.onFlowGroupStoped(ctx))
      }

      override def onProjectStoped(ctx: ProjectContext): Unit = {
        listeners.foreach(_.onProjectStoped(ctx))
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

    override def start(flowGroup: FlowGroup): FlowGroupExecution = {
      new FlowGroupExecutionImpl(flowGroup, ctx, this);
    }

    override def start(project: Project): ProjectExecution = {
      new ProjectExecutionImpl(project, ctx, this);
    }

    override def removeListener(listener: RunnerListener): Unit = {
      listeners -= listener;
    }
  }
}

trait RunnerListener {
  def
  onProcessStarted(ctx: ProcessContext);

  def onProcessForked(ctx: ProcessContext, child: ProcessContext);

  def onProcessCompleted(ctx: ProcessContext);

  def onProcessFailed(ctx: ProcessContext);

  def onProcessAborted(ctx: ProcessContext);

  def onJobInitialized(ctx: JobContext);

  def onJobStarted(ctx: JobContext);

  def onJobCompleted(ctx: JobContext);

  def onJobFailed(ctx: JobContext);

  def monitorJobCompleted(ctx: JobContext,outputs : JobOutputStream);

  def onFlowGroupStarted(ctx: FlowGroupContext);

  def onFlowGroupCompleted(ctx: FlowGroupContext);

  def onFlowGroupFailed(ctx: FlowGroupContext);

  def onFlowGroupStoped(ctx: FlowGroupContext);

  def onProjectStarted(ctx: ProjectContext);

  def onProjectCompleted(ctx: ProjectContext);

  def onProjectFailed(ctx: ProjectContext);

  def onProjectStoped(ctx: ProjectContext);
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

  override def onFlowGroupStarted(ctx: FlowGroupContext): Unit = {
    //TODO: write monitor data into db
    val groupId = ctx.getFlowGroupExecution().groupId()
    val flowGroupName = ctx.getFlowGroup().getFlowGroupName()
    val time = new Date().toString
    logger.debug(s"Flow Group started: $groupId, flow group: $flowGroupName, time: $time");
    println(s"Flow Group started: $groupId, flow group: $flowGroupName, time: $time")
    //update flow group state to STARTED
    H2Util.addFlowGroup(groupId, flowGroupName)
    H2Util.updateFlowGroupState(groupId,FlowGroupState.STARTED)
    H2Util.updateFlowGroupStartTime(groupId,time)
  }

  override def onFlowGroupCompleted(ctx: FlowGroupContext): Unit = {
    //TODO: write monitor data into db
    val groupId = ctx.getFlowGroupExecution().groupId()
    val flowGroupName = ctx.getFlowGroup().getFlowGroupName()
    val time = new Date().toString
    logger.debug(s"Flow Group completed: $groupId, time: $time");
    println(s"Flow Group completed: $groupId, time: $time")
    //update flow group state to COMPLETED
    H2Util.updateFlowGroupState(groupId,FlowGroupState.COMPLETED)
    H2Util.updateFlowGroupFinishedTime(groupId,time)
  }

  override def onFlowGroupStoped(ctx: FlowGroupContext): Unit = {
    //TODO: write monitor data into db
    val groupId = ctx.getFlowGroupExecution().groupId()
    val flowGroupName = ctx.getFlowGroup().getFlowGroupName()
    val time = new Date().toString
    logger.debug(s"Flow Group stoped: $groupId, time: $time");
    println(s"Flow Group stoped: $groupId, time: $time")
    //update flow group state to COMPLETED
    H2Util.updateFlowGroupState(groupId,FlowGroupState.KILLED)
    H2Util.updateFlowGroupFinishedTime(groupId,time)

  }

  override def onFlowGroupFailed(ctx: FlowGroupContext): Unit = {
    //TODO: write monitor data into db
    val groupId = ctx.getFlowGroupExecution().groupId()
    val flowGroupName = ctx.getFlowGroup().getFlowGroupName()
    val time = new Date().toString
    logger.debug(s"Flow Group failed: $groupId, time: $time");
    println(s"Flow Group failed: $groupId, time: $time")
    //update flow group state to FAILED
    H2Util.updateFlowGroupState(groupId,FlowGroupState.FAILED)
    H2Util.updateFlowGroupFinishedTime(groupId,time)
  }

  override def onProjectStarted(ctx: ProjectContext): Unit = {
    //TODO: write monitor data into db
    val projectId = ctx.getProjectExecution().projectId()
    val projectName = ctx.getProject().getProjectName()
    val time = new Date().toString
    logger.debug(s"Project started: $projectId, project: $projectName, time: $time");
    println(s"Project started: $projectId, project: $projectName, time: $time")
    //update project state to STARTED
    H2Util.addProject(projectId, projectName)
    H2Util.updateProjectState(projectId,ProjectState.STARTED)
    H2Util.updateProjectStartTime(projectId,time)
  }

  override def onProjectCompleted(ctx: ProjectContext): Unit = {
    //TODO: write monitor data into db
    val projectId = ctx.getProjectExecution().projectId()
    val projectName = ctx.getProject().getProjectName()
    val time = new Date().toString
    logger.debug(s"Project completed: $projectId, time: $time");
    println(s"Project completed: $projectId, time: $time")
    //update project state to COMPLETED
    H2Util.updateProjectState(projectId,ProjectState.COMPLETED)
    H2Util.updateProjectFinishedTime(projectId,time)
  }

  override def onProjectFailed(ctx: ProjectContext): Unit = {
    //TODO: write monitor data into db
    val projectId = ctx.getProjectExecution().projectId()
    val projectName = ctx.getProject().getProjectName()
    val time = new Date().toString
    logger.debug(s"Project failed: $projectId, time: $time");
    println(s"Project failed: $projectId, time: $time")
    //update project state to FAILED
    H2Util.updateProjectState(projectId,ProjectState.FAILED)
    H2Util.updateProjectFinishedTime(projectId,time)
  }



  override def onProjectStoped(ctx: ProjectContext): Unit = {
    val projectId = ctx.getProjectExecution().projectId()
    val projectName = ctx.getProject().getProjectName()
    val time = new Date().toString
    logger.debug(s"Project failed: $projectId, time: $time");
    println(s"Project failed: $projectId, time: $time")
    //update project state to FAILED
    H2Util.updateProjectState(projectId,ProjectState.KILLED)
    H2Util.updateProjectFinishedTime(projectId,time)

  }
}
