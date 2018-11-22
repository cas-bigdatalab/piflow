package cn.piflow

import java.util.Date

import cn.piflow.util.{FlowState, H2Util, Logging, StopState}
import org.apache.spark.sql.SparkSession

import scala.collection.mutable.ArrayBuffer

trait Runner {
  def bind(key: String, value: Any): Runner;

  def start(flow: Flow): Process;

  def start(flowGroup: FlowGroup): FlowGroupExecution;

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
}

class RunnerLogger extends RunnerListener with Logging {
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
}
