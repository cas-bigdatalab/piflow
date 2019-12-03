package cn.piflow.api

import cn.piflow.Runner
import cn.piflow.api.util.PropertyUtil
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.OptionUtil
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
    val spark = SparkSession.builder()
      .appName(flowBean.name)
      .config("hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .enableHiveSupport()
      .getOrCreate()

    println("hive.metastore.uris=" + spark.sparkContext.getConf.get("hive.metastore.uris") + "!!!!!!!")
    //val checkpointPath = spark.sparkContext.getConf.get("checkpoint.path")

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      //.bind("checkpoint.path","hdfs://10.0.86.89:9000/xjzhu/piflow/checkpoints/")
      //.bind("debug.path","hdfs://10.0.86.89:9000/xjzhu/piflow/debug/")
      .bind("checkpoint.path",PropertyUtil.getPropertyValue("checkpoint.path"))
      .bind("debug.path",PropertyUtil.getPropertyValue("debug.path"))
      .start(flow);
    val applicationId = spark.sparkContext.applicationId
    process.awaitTermination();
    spark.close();
    /*new Thread( new WaitProcessTerminateRunnable(spark, process)).start()
    (applicationId,process)*/
  }

}
