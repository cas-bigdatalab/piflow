package cn.piflow.bundle

import java.util.ArrayList

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.jsoup.Jsoup
import org.jsoup.select.Elements
import org.junit.Test
import org.neo4j.driver.v1._

import scala.util.parsing.json.JSON

class BioGroupDataTest {

  @Test
  def testBioProjetDataParse(): Unit ={

    //parse flow json
    val file = "src/main/resources/bioProject.json"
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
      .appName("BioProjetDataParse")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("spark.jars","/work4/hbase/out/artifacts/piflow_bundle/piflow_bundle.jar")
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
  def testgenurl222(): Unit ={
    val spark = SparkSession.builder()
      .master("local[4]")
      .appName("BioProjetDataParse")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .enableHiveSupport()
      .getOrCreate()

    var url : String = "bolt://192.168.3.140:7687"
    var userName : String = "neo4j"
    var password : String = ""
    var cql : String ="USING PERIODIC COMMIT 10000 LOAD CSV WITH HEADERS FROM 'http://192.168.3.138:50070/webhdfs/v1/piflow-CSV-of-Neo4j/Organization/organization.csv?op=OPEN' AS line FIELDTERMINATOR '¤' CREATE (:Organization:OrganizationSelf {organizationID:line.org_code,organization:line.name,city:line.city,province:line.province,organizationType:line.orgtype,\nareaNo:line.area_no,\ncreateDate:line.create_date,\ncontactPersonID:line.contact_psn_code,\nnatureType:line.nature_type,\nnature:line.nature,\nbelongNet:line.belongnet,\napproveNO:line.pno,\nzipCode:line.zipcode,\nregYear:line.regyear,\nenglishName:line.en_name,\ndisplay:toBoolean('true')})"
    var openTransaction : Boolean = false


    val cqls: Array[String] = cql.split(";")

    var driver: Driver = GraphDatabase.driver(url, AuthTokens.basic(userName, password))
    var session: Session = null
    var transaction: Transaction = null
    var n = 0

    if (openTransaction) {
      try {
        session = driver.session()
        transaction = session.beginTransaction()
        cqls.foreach(eachCql => {
          n += 1
          transaction.run(eachCql)
          transaction.success()
          if (n == 50) {
            transaction.close()
            transaction = session.beginTransaction()
            n = 0
          }
        })
      } finally {
        transaction.close()
        session.close()
        driver.close()
      }
    } else {
      try {
        session = driver.session()
        session.run(cqls(0))
      } finally {
        session.close()
        driver.close()
      }
    }




  }





  @Test
  def testgenurl(): Unit ={

    val url = "https://ftp.ncbi.nlm.nih.gov/bioproject/"
    val url1 =  "https://ftp.ncbi.nih.gov/genbank"

  var filePathList = new ArrayList[String]

    val doc = Jsoup.connect(url).timeout(100000000).get()
    //  获取 url 界面   文件名字  日期   大小
    //  Name                    Last modified      Size  Parent Directory                             -
    //  build_gbff_cu.pl        2003-04-25 17:23   21K

    val elements: Elements = doc.select("html >body >pre")
    println(elements.first().text())
  }

}
