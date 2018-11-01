package cn.piflow.bundle

import cn.piflow.Runner
import cn.piflow.bundle.util.UnGzUtil
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.{JSON, JSONObject}

class GenBankTest {

  @Test
  def testSeq(): Unit ={

    //parse flow json
    val file = "src/main/resources/genbank.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort","50001").start()
    //execute flow
    val spark = SparkSession.builder()
      .master("spark://10.0.86.89:7077")
      .appName("es")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("spark.jars","/opt/project/piflow-master/out/artifacts/piflow_bundle/piflow_bundle.jar")
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



  @Test
  def testGz(): Unit ={
    val inputDir = "/ftpUrlDownLoad111/gbbct11.seq.gz"
    val savePath = "/ftpUrlDownLoad111/"
    val fileName = "gbbct11.seq"

    val a = UnGzUtil.unGz(inputDir,savePath,fileName)
    println(a)


  }

}
