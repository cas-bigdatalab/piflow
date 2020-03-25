package cn.piflow.bundle.common

import java.net.InetAddress

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import cn.piflow.util.{PropertyUtil, ServerIpUtil}
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

class DropFieldTest {

  @Test
  def testFlow(): Unit ={

    //parse flow json
    val file = "src/main/resources/flow/common/dropField.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()


    val ip = InetAddress.getLocalHost.getHostAddress
    cn.piflow.util.FileUtil.writeFile("server.ip=" + ip, ServerIpUtil.getServerIpFile())
    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort","50001").start()
    //execute flow
    val spark = SparkSession.builder()
      .master("local[12]")
      .appName("hive")
      .config("spark.driver.memory", "4g")
      .config("spark.executor.memory", "8g")
      .config("spark.cores.max", "8")
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
