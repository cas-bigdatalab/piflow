package cn.piflow

import cn.piflow.util.Logging

import scala.collection.mutable.ArrayBuffer

trait Runner {
  def bind(key: String, value: Any): Runner;

  def start(flow: Flow): Process;

  def start(flowGroup: FlowGroup): FlowGroupExecution;

  def addListener(listener: RunnerListener);

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
    logger.debug(s"process started: $pid, flow: $flowName");
  };

  override def onJobStarted(ctx: JobContext): Unit = {
    val jid = ctx.getStopJob().jid();
    val stopName = ctx.getStopJob().getStopName();
    logger.debug(s"job started: $jid, stop: $stopName");
  };

  override def onJobFailed(ctx: JobContext): Unit = {
    val stopName = ctx.getStopJob().getStopName();
    logger.debug(s"job failed: $stopName");
  };

  override def onJobInitialized(ctx: JobContext): Unit = {
    val stopName = ctx.getStopJob().getStopName();
    logger.debug(s"job initialized: $stopName");
  };

  override def onProcessCompleted(ctx: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    logger.debug(s"process completed: $pid");
  };

  override def onJobCompleted(ctx: JobContext): Unit = {
    val stopName = ctx.getStopJob().getStopName();
    logger.debug(s"job completed: $stopName");
  };

  override def onProcessFailed(ctx: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    logger.debug(s"process failed: $pid");
  }

  override def onProcessAborted(ctx: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    logger.debug(s"process aborted: $pid");
  }

  override def onProcessForked(ctx: ProcessContext, child: ProcessContext): Unit = {
    val pid = ctx.getProcess().pid();
    val cid = child.getProcess().pid();
    logger.debug(s"process forked: $pid, child flow execution: $cid");
  }
}
