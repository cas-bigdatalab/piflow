package cn.piflow.api

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.OptionUtil
import cn.piflow.util.{ConfigureUtil, PropertyUtil}
import org.apache.spark.sql.SparkSession

import scala.util.parsing.json.JSON

object StartFlowMain {

  def main(args: Array[String]): Unit = {
    val flowJson = args(0)

    println(flowJson)
    val map = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    //execute flow
    val sparkSessionBuilder = SparkSession.builder().appName(flowBean.name)
    if(PropertyUtil.getPropertyValue("hive.metastore.uris") != null){

      sparkSessionBuilder
        .config("hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
        .enableHiveSupport()
    }
    val spark = sparkSessionBuilder.getOrCreate()
    //println("hive.metastore.uris=" + spark.sparkContext.getConf.get("hive.metastore.uris") + "!!!!!!!")

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path",ConfigureUtil.getCheckpointPath())
      .bind("debug.path",ConfigureUtil.getDebugPath())
      .start(flow);
    val applicationId = spark.sparkContext.applicationId
    process.awaitTermination();
    spark.close();
    /*new Thread( new WaitProcessTerminateRunnable(spark, process)).start()
    (applicationId,process)*/
  }

}
