package cn.piflow.util

import cn.piflow.Flow
import org.apache.flink.streaming.api.scala.StreamExecutionEnvironment

object FlinkLauncher {

  def launch(flow: Flow) : StreamExecutionEnvironment = {

    //val env = ExecutionEnvironment.getExecutionEnvironment
    //val env = StreamExecutionEnvironment.createLocalEnvironment(1)
    val env = StreamExecutionEnvironment.createRemoteEnvironment(
      PropertyUtil.getPropertyValue("flink.host"),
      PropertyUtil.getPropertyValue("flink.port").toInt,
      ConfigureUtil.getPiFlowBundlePath())

    env
  }

}
