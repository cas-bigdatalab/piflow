package cn.piflow.bundle

import cn.piflow.Runner
import cn.piflow.bundle.util.UnGzUtil
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

class TaxonomyTest {

  @Test
  def testTaxonomy(): Unit ={

    //parse flow json
    val file = "src/main/resources/taxonomy001.json"
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
      .appName("Taxonomy")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("spark.jars","/workFtp/1128/out/artifacts/piflow_bundle/piflow_bundle.jar")
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
  def test221(): Unit ={
    val inputDir = "/ftpTaxonomy/apache.ar.gz"

    if (inputDir.endsWith("tar.gz")) {
      println("tar.gz")
    } else if (inputDir.endsWith(".gz")){
      println(".gz")
    }


  }

  @Test
  def testUngz11(): Unit ={
    val inputDir = "/ftpTaxonomy/apache.tar.gz"
    val inputDir1 = "/ftpTaxonomy/taxdump.tar.gz"
    val savePath="/ftpTaxonomy/"
    val filename = "biosample.xml"
    val strings = UnGzUtil.unTarGz(inputDir,savePath)
    println(strings.size())

  }



  @Test
  def testUngz(): Unit ={





    val inputDir ="/ftpBioSample/biosample.xml.gz"
    val savePath="/ftpBioSample/"
    val filename = "biosample.xml"

    val filePath: String = UnGzUtil.unGz(inputDir,savePath,filename)
    println("解压完成----->"+filePath)
  }

}
