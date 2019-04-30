package cn.piflow.api

import cn.piflow.{Flow, Runner}
import cn.piflow.api.util.PropertyUtil
import cn.piflow.conf.bean.FlowGroupBean
import cn.piflow.conf.util.OptionUtil
import org.apache.spark.sql.SparkSession

import scala.collection.mutable.ArrayBuffer
import scala.util.parsing.json.JSON

object StartFlowGroupMain {

  def main(args: Array[String]): Unit = {
    val flowGroupJson = args(0)
    println(flowGroupJson)
    val map = OptionUtil.getAny(JSON.parseFull(flowGroupJson)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flowGroup
    val flowGroupBean = FlowGroupBean(map)
    val flowGroup = flowGroupBean.constructFlowGroup()

    //execute flow
    val spark = SparkSession.builder()
      .appName(flowGroupBean.name)
      .enableHiveSupport()
      .getOrCreate()
    //val checkpointPath = spark.sparkContext.getConf.get("checkpoint.path")

    val process = Runner.create()
      //.bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path",PropertyUtil.getPropertyValue("checkpoint.path"))
      .bind("debug.path",PropertyUtil.getPropertyValue("debug.path"))
      .start(flowGroup);
    val applicationId = spark.sparkContext.applicationId
    process.awaitTermination();
    spark.close();
    /*new Thread( new WaitProcessTerminateRunnable(spark, process)).start()
    (applicationId,process)*/
  }

}
