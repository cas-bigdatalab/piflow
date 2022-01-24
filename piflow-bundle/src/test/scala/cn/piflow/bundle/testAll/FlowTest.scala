package cn.piflow.bundle.testAll

import java.net.InetAddress

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import cn.piflow.util.ServerIpUtil
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

class FlowTest {

  @Test
  def testFlow(): Unit ={

    //parse flow json
    val file = "src/main/resources/flow_route.json"
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
      .master("local")
      .appName("piflow-hive-bundle-xjzhu")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("hive.metastore.uris","thrift://10.0.86.191:9083")
      //.config("spark.jars","/opt/project/piflow/out/artifacts/piflow_bundle/piflow-bundle.jar")
      .enableHiveSupport()
      .getOrCreate()
//    val spark = SparkSession.builder()
//      .master("yarn")
//      .appName(flowBean.name)
//      .config("spark.deploy.mode","cluster")
//      .config("spark.hadoop.yarn.resourcemanager.hostname", "10.0.86.191")
//      .config("spark.hadoop.cdefnprst.resourcemanager.address", "10.0.86.191:8032")
//      .config("spark.yarn.access.namenode", "hdfs://10.0.86.191:9000")
//      .config("spark.yarn.stagingDir", "hdfs://10.0.86.191:9000/tmp")
//      .config("spark.yarn.jars", "hdfs://10.0.86.191:9000/user/spark/share/lib/*.jar")
//      //.config("spark.driver.memory", "1g")
//      //.config("spark.executor.memory", "1g")
//      //.config("spark.cores.max", "2")
//      .config("spark.jars", "/opt/project/piflow/piflow-server/target/piflow-server-0.9.jar")
//      .config("hive.metastore.uris","thrift://10.0.86.191:9083")
//      .enableHiveSupport()
//      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "hdfs://10.0.86.89:9000/xjzhu/piflow/checkpoints/")
      .bind("debug.path","hdfs://10.0.86.89:9000/xjzhu/piflow/debug/")
      .start(flow);

    process.awaitTermination();
    val pid = process.pid();
    println(pid + "!!!!!!!!!!!!!!!!!!!!!")
    spark.close();
  }

  /*@Test
  def testFlow2json() = {

    //parse flow json
    val file = "src/main/resources/flow.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]

    //create flow
    val flowBean = FlowBean(map)
    val flowJson = flowBean.toJson()
    println(flowJson)
  }*/

}
