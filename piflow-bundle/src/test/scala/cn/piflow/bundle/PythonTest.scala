package cn.piflow.bundle

import java.net.InetAddress

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import cn.piflow.util.ServerIpUtil
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

/**
  * Created by xjzhu@cnic.cn on 2/24/20
  */
class PythonTest {

  @Test
  def testPython() : Unit = {
    //parse flow json
    val file = "src/main/resources/python.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    //execute flow
    val spark = SparkSession.builder()
      .master("local")
      //.master("spark://10.0.86.89:7077")
      .appName("pythonTest")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      //.config("spark.jars","/opt/project/piflow/piflow-bundle/lib/jython-standalone-2.7.1.jar")
      .enableHiveSupport()
      .getOrCreate()

    val ip = InetAddress.getLocalHost.getHostAddress
    cn.piflow.util.FileUtil.writeFile("server.ip=" + ip, ServerIpUtil.getServerIpFile())
    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort","50001").start()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "hdfs://10.0.86.89:9000/xjzhu/piflow/checkpoints/")
      .bind("debug.path","hdfs://10.0.86.89:9000/xjzhu/piflow/debug/")
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

}
