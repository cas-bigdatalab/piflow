package cn.piflow.util

import cn.piflow.util._


object StateUtil {

  val yarnInitState = List(FlowYarnState.NEW, FlowYarnState.NEW_SAVING, FlowYarnState.SUBMITTED, FlowYarnState.ACCEPTED)
  val yarnStartedState = List(FlowYarnState.RUNNING)
  val yarnCompletedState = List(FlowYarnState.FINISHED)
  val yarnFailedState = List(FlowYarnState.FAILED)
  val yarnKilledState = List(FlowYarnState.KILLED)

  def FlowStateCheck(flowState: String, flowYarnState: String) : Boolean = {

    if(flowState == FlowState.INIT && yarnInitState.contains(flowYarnState)){
      true
    }else if(flowState == FlowState.STARTED && yarnStartedState.contains(flowYarnState)){
      true
    }else if(flowState == FlowState.COMPLETED && yarnCompletedState.contains(flowYarnState)){
      true
    }else if(flowState == FlowState.FAILED && yarnFailedState.contains(flowYarnState)){
      true
    }else if(flowState == FlowState.KILLED && yarnKilledState.contains(flowYarnState)){
      true
    }else{
      false
    }

  }

  def getNewFlowState(flowState: String, flowYarnState: String) : String = {

    if(yarnStartedState.contains(flowYarnState)){
      FlowState.STARTED
    }else if(yarnCompletedState.contains(flowYarnState)){
      FlowState.COMPLETED
    }else if(yarnFailedState.contains(flowYarnState)){
      FlowState.FAILED
    }else if(yarnKilledState.contains(flowYarnState)){
      FlowState.KILLED
    }else{
      ""
    }
  }

}
