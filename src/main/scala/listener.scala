/**
  * Created by bluejoe on 2018/5/10.
  */
package cn.piflow

trait FlowExecutionListener {
  def onFlowStarted(execution: FlowExecution);

  def onFlowShutdown(execution: FlowExecution);

  def onEventFired(event: Event, args: Any, execution: FlowExecution);

  def onProcessStarted(processName: String, process: Process, execution: FlowExecution);

  def onProcessCompleted(processName: String, process: Process, execution: FlowExecution);

  def onProcessFailed(processName: String, process: Process, cause: Exception, execution: FlowExecution);
}
