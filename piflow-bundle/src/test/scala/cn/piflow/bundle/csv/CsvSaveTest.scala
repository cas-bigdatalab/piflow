package cn.piflow.bundle.csv

import cn.piflow.bundle.json.JsonSave
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import cn.piflow.util.PropertyUtil
import cn.piflow.{FlowImpl, Path, Runner}
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

class CsvSaveTest {

  @Test
  def CsvSaveAsAppendFlow(): Unit ={

    //parse flow json
    val file = "src/main/resources/flow/csv/CsvSaveAsAppend.json"
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
      .appName("CsvSaveTest")
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

  @Test
  def CsvSaveAsOverWriteFlow(): Unit ={

    //parse flow json
    val file = "src/main/resources/flow/csv/CsvSaveAsOverWrite.json"
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
      .appName("piflow-hive-bundle")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("hive.metastore.uris", PropertyUtil.getPropertyValue("hive.metastore.uris"))
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

  @Test
  def CsvSaveAsErrorFlow(): Unit ={

    //parse flow json
    val file = "src/main/resources/flow/csv/CsvSaveAsError.json"
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
      .appName("piflow-hive-bundle")
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
  @Test
  def CsvSaveAsIgnoreFlow(): Unit ={

    //parse flow json
    val file = "src/main/resources/flow/csv/CsvSaveAsIgnore.json"
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
      .appName("piflow-hive-bundle")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("hive.metastore.uris", PropertyUtil.getPropertyValue("hive.metastore.uris"))
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
