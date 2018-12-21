package cn.piflow.bundle.ftp

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.jsoup.Jsoup
import org.jsoup.select.Elements
import org.junit.Test

import scala.util.parsing.json.JSON

class emblTest {

  @Test
  def testEmblDataParse(): Unit ={

    //parse flow json
//    val file = "src/main/resources/yqd/down.json"
//val file = "src/main/resources/yqd/refseq_genome.json"
//val file = "src/main/resources/yqd/select_unzip.json"
val file = "src/main/resources/yqd/embl_parser.json"

    val flowJsonStr = FileUtil.fileReader(file)

    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort","50001").start()
    //execute flow
    val spark = SparkSession.builder()
      .master("spark://10.0.88.70:7077")
      .appName("Embl")
      .config("spark.driver.memory", "8g")
      .config("spark.executor.memory", "16g")
      .config("spark.cores.max", "16")
      .config("spark.jars","/root/Desktop/weishengwu/out/artifacts/piflow_bundle/piflow_bundle.jar")
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
  def testEmblDataParse11(): Unit ={

    val url ="http://ftp.ebi.ac.uk/pub/databases/ena/sequence/release/"
    val doc = Jsoup.connect(url).timeout(100000000).get()
    //  获取 url 界面   文件名字  日期   大小
    //  Name                    Last modified      Size  Parent Directory                             -
    //  build_gbff_cu.pl        2003-04-25 17:23   21K

    val elements: Elements = doc.select("html >body >table >tbody")
//    println(elements)
    println(elements.first().text())

    // 按行 分割 elements 为单个字符串
    val fileString = elements.first().text().split("\\n")


    for (i <- 0 until fileString.size) {

     println(fileString(i))
    }

    println(fileString)
  }





}
