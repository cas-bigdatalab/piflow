package cn.piflow.bundle.ftp

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

class emblTest {

  @Test
  def testEmblDataParse(): Unit ={

    //parse flow json
//    val file = "src/main/resources/yqd/down.json"
//val file = "src/main/resources/yqd/refseq_genome.json"
//val file = "src/main/resources/yqd/select_unzip.json"
val file = "src/main/resources/microorganism/gene.json"

    val flowJsonStr = FileUtil.fileReader(file)

    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort","50001").start()
    //execute flow
    val spark = SparkSession.builder()
      .master("yarn")
      .appName("test18")
      .config("spark.deploy.mode","client")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "4")
      .config("hive.metastore.uris","thrift://10.0.88.64:9083")
      .config("spark.yarn.am.extraJavaOptions","-Dhdp.version=2.6.5.0-292")
      .config("spark.hadoop.yarn.resourcemanager.address","master2.packone:8050")
      .config("spark.hadoop.fs.defaultFS","hdfs://master2.packone:8020")
      .config("spark.jars","/git_1225/out/artifacts/piflow/piflow.jar")
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "hdfs://10.0.86.89:9000/xjzhu/piflow/checkpoints/")
      .start(flow);

    process.awaitTermination();
    val pid = process.pid();
    println(pid + "!!!!!!!!!!!!!!!!!!!!!")
    spark.close();
  }



}
