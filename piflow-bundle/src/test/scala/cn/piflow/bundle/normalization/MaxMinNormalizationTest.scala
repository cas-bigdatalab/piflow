//package cn.piflow.bundle.normalization
//
//import cn.piflow.Runner
//import cn.piflow.conf.bean.FlowBean
//import cn.piflow.conf.util.{FileUtil, OptionUtil}
//import org.apache.spark.sql.SparkSession
//import org.junit.Test
//import scala.util.parsing.json.JSON
//
//class MaxMinNormalizationTest {
//
//  @Test
//  def MaxMinNormalizationTest(): Unit = {
//    // Parse flow JSON
//    val file = "src/main/resources/flow/normalization/MaxMinNormalization.json"
//    val flowJsonStr = FileUtil.fileReader(file)
//    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
//    println(map)
//
//    // Create SparkSession
//    val spark = SparkSession.builder()
//      .master("local[*]")
//      .appName("MaxMinNormalizationTest")
//      .config("spark.driver.memory", "1g")
//      .config("spark.executor.memory", "2g")
//      .config("spark.cores.max", "2")
//      .getOrCreate()
//
//    // Create flow
//    val flowBean = FlowBean(map)
//    val flow = flowBean.constructFlow()
//
//    // Execute flow
//    val process = Runner.create()
//      .bind(classOf[SparkSession].getName, spark)
//      .bind("checkpoint.path", "")
//      .bind("debug.path", "")
//      .start(flow)
//
//    process.awaitTermination()
//    val pid = process.pid()
//    println(s"Flow execution completed. PID: $pid")
//
//    // Close SparkSession
//    spark.close()
//  }
//}


package cn.piflow.bundle.normalization

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import cn.piflow.util.PropertyUtil
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

class MaxMinNormalizationTest {

  @Test
  def MaxMinNormalizationFlow(): Unit = {

    //parse flow json
    val file = "src/main/resources/flow/normalization/MaxMinNormalization.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort", "50001").start()

    //execute flow
    val spark = SparkSession.builder()
      .master("local[*]")
      .appName("MaxMinNormalizationTest")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "")
      .bind("debug.path","")
      .start(flow);

    process.awaitTermination();
    val pid = process.pid();
    println(pid + "!!!!!!!!!!!!!!!!!!!!!")
    spark.close();
  }
}
