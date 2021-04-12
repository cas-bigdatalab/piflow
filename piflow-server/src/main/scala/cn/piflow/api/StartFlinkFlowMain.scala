package cn.piflow.api

import java.io.File

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.OptionUtil
import cn.piflow.util.{ConfigureUtil, FlowFileUtil, PropertyUtil}
import org.apache.flink.api.scala.ExecutionEnvironment
import org.apache.flink.streaming.api.scala.StreamExecutionEnvironment
import org.apache.spark.sql.SparkSession

import scala.util.parsing.json.JSON

object StartFlinkFlowMain {

  def main(args: Array[String]): Unit = {

    /*val flowFileName = args(0)

    var flowFilePath= FlowFileUtil.getFlowFileInUserDir(flowFileName)
    val file = new File(flowFilePath)
    if(!file.exists()){
      flowFilePath = FlowFileUtil.getFlowFilePath(flowFileName)
    }

    val flowJson = FlowFileUtil.readFlowFile(flowFilePath).trim()*/
    val flowJson = args(0)
    println(flowJson)
    val map = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow(false)


    val env = StreamExecutionEnvironment.getExecutionEnvironment
    val process = Runner.create()
      .bind(classOf[StreamExecutionEnvironment].getName, env)
      .start(flow);

  }

}
