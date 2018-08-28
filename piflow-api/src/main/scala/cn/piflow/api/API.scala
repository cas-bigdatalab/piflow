package cn.piflow.api

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import org.apache.spark.sql.SparkSession
import cn.piflow.conf.util.OptionUtil
import cn.piflow.Process

import scala.util.parsing.json.JSON

object API {

  def startFlow(flowJson : String):Process = {
    //parse flow json
    val map = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    //execute flow
    val spark = SparkSession.builder()
      .master("spark://10.0.86.89:7077")
      .appName("piflow-hive-bundle")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("spark.jars", "/opt/project/piflow/out/artifacts/piflow_bundle/piflow-bundle.jar")
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "hdfs://10.0.86.89:9000/xjzhu/piflow/checkpoints/")
      .start(flow);

    process.awaitTermination();
    spark.close();
    process
  }

  def stopFlow(process : Process): String = {
    process.stop()
    "ok"
  }
}
