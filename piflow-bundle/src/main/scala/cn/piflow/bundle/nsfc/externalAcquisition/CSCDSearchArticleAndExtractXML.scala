package cn.piflow.bundle.nsfc.externalAcquisition

import java.net.URL

import cn.piflow.bundle.util.XMLBuilder
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import com.cscd.webservice.CscdService
import javax.xml.namespace.QName
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Row, SparkSession}
import org.w3c.dom.Document

import scala.collection.JavaConverters._
import scala.collection.mutable


/**
  * Created by SongDz on 2019/7/24.
  *
  * @author SongDz
  */
class CSCDSearchArticleAndExtractXML extends ConfigurableStop {

  val authorEmail: String = "songdongze@cnic.cn"
  val description: String = "CSCD Search Article And Extract XML"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  val xpath_expressions: List[String] = List("/articles/article/cscd_id", "/articles/article/title", "/articles/article/authorlist/author/author_name", "/articles/article/authorlist/author/institute", "/articles/article/journal/journal_name", "/articles/article/issue/volume", "/articles/article/issue/year", "/articles/article/page_string", "/articles/article/journal/issn", "/articles/article/issue/issue", "/articles/article/cited_num", "/articles/article/keywords", "/articles/article/doi", "/articles/article/abstract")

  //var database:String = _
  //var table:String = _
  var wsdl_url: String = _
  var user_name: String = _
  var password: String = _

  case class Article(cscd_id: String, title: String, author_name: String, author_institute: String, journal: String, volume: String, year: String, page_string: String, issn: String, issue: String, cited_num: String, keywords: String, doi: String, `abstract`: String)

  val schema: StructType = StructType(List(
    StructField("cscd_id", StringType, nullable = false),
    StructField("title", StringType, nullable = true),
    StructField("author_name", StringType, nullable = true),
    StructField("author_institute", StringType, nullable = true),
    StructField("journal", StringType, nullable = true),
    StructField("volume", StringType, nullable = true),
    StructField("year", StringType, nullable = true),
    StructField("page_string", StringType, nullable = true),
    StructField("issn", StringType, nullable = true),
    StructField("issue", StringType, nullable = true),
    StructField("cited_num", StringType, nullable = true),
    StructField("keywords", StringType, nullable = true),
    StructField("doi", StringType, nullable = true),
    StructField("abstract", StringType, nullable = true)
  ))

  def setProperties(map: Map[String, Any]): Unit = {
    //database = MapUtil.get(map,"database").asInstanceOf[String]
    //table = MapUtil.get(map,"table").asInstanceOf[String]
    wsdl_url = MapUtil.get(map, "wsdl_url").asInstanceOf[String]
    user_name = MapUtil.get(map, "user_name").asInstanceOf[String]
    password = MapUtil.get(map, "password").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    //val database=new PropertyDescriptor().name("database").displayName("DataBase").description("The database name").defaultValue("").required(true)
    //val table = new PropertyDescriptor().name("table").displayName("Table").description("The table name").defaultValue("").required(true)
    val wsdl_url = new PropertyDescriptor().name("wsdl_url").displayName("WSDL_URL").description("The CSCD WSDL URL").defaultValue("").required(true)
    val user_name = new PropertyDescriptor().name("user_name").displayName("User Name").description("The CSCD user name").defaultValue("").required(true)
    val password = new PropertyDescriptor().name("password").displayName("Password").description("The CSCD user password").defaultValue("").required(true)
    //descriptor = database :: descriptor
    //descriptor = table :: descriptor
    descriptor = wsdl_url :: descriptor
    descriptor = user_name :: descriptor
    descriptor = password :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/nsfc/cscd.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.NSFC.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val inDF = in.read()
    val SERVICE_NAME = new QName("http://webservice.cscd.com", "CscdService")
    var wsdlURL = CscdService.WSDL_LOCATION
    if (wsdl_url != null && !wsdl_url.equals("")) {
      wsdlURL = new URL(wsdl_url)
    }
    val ss = new CscdService(wsdlURL, SERVICE_NAME)
    val port = ss.getCscdServiceHttpSoap11Endpoint
    val name = user_name
    val passwd = password


    val newDF = inDF.coalesce(5)
    println("---rdd partitions num---")
    println(newDF.rdd.getNumPartitions)
    val rdd: RDD[Row] = newDF.rdd.mapPartitions[Row](f => {
      //println(TaskContext.get.partitionId())
      val collect_f = f.toSeq
      val _ss = new CscdService(wsdlURL, SERVICE_NAME)
      val _port = _ss.getCscdServiceHttpSoap11Endpoint
      val schema_xpathExpressions: Map[String, String] = Map("cscd_id" -> "/articles/article/cscd_id", "title" -> "/articles/article/title", "author_name" -> "/articles/article/authorlist/author/author_name", "author_institute" -> "/articles/article/authorlist/author/institute", "journal" -> "/articles/article/journal/journal_name", "volume" -> "/articles/article/issue/volume", "year" -> "/articles/article/issue/year", "page_string" -> "/articles/article/page_string", "issn" -> "/articles/article/journal/issn", "issue" -> "/articles/article/issue/issue", "cited_num" -> "/articles/article/cited_num", "keywords" -> "/articles/article/keywords", "doi" -> "/articles/article/doi", "abstract" -> "/articles/article/abstract")
      val _code = _port.getCode(name, passwd)
      if (!_code.equals("No Access")) {
        collect_f.map(r => {
          //println(r.getString(0))
          try {
            val cscdIdsXmlString = _port.searchArticles(_code, "", "", r.get(0).toString, "")
           /* println("----------")
            println(cscdIdsXmlString)
            println("----------")*/
            val document = XMLBuilder.buildDocument(cscdIdsXmlString)
            val cscdIdsList = XMLBuilder.getNodeByXPath(document, "/result/cscd_id")
            if (cscdIdsList.size == 1) {
              val article = _port.getArticles(_code, cscdIdsList.get(0))
              /*println("----------")
              println("getArticles.result=" + article)
              println("----------")*/

              val articleDocument = XMLBuilder.buildDocument(article)

              val xmlInfo: mutable.Map[String, String] = XMLBuilder.getNodeByXPath(articleDocument, schema_xpathExpressions.asJava).asScala
              Row.fromTuple((xmlInfo("cscd_id"), xmlInfo("title"), xmlInfo("author_name"), xmlInfo("author_institute"), xmlInfo("journal"), xmlInfo("volume"), xmlInfo("year"), xmlInfo("page_string"), xmlInfo("issn"), xmlInfo("issue"), xmlInfo("cited_num"), xmlInfo("keywords"), xmlInfo("doi"), xmlInfo("abstract")))
            } else if (cscdIdsList.size > 1) {
              var flag: Boolean = true
              var i: Int = 0
              var row: Row = null
              while (flag && i < cscdIdsList.size()) {
                val article: String = _port.getArticles(_code, cscdIdsList.get(i))
                /*println("----------")
                println("getArticles.result=" + article)
                println("----------")*/
                val articleDocument: Document = XMLBuilder.buildDocument(article)
                val title: String = XMLBuilder.getNodeByXPath(articleDocument, "/articles/article/title").get(0)
                if (r.get(0).toString.equals(title)) {
                  val xmlInfo: mutable.Map[String, String] = XMLBuilder.getNodeByXPath(articleDocument, schema_xpathExpressions.asJava).asScala
                  row = Row.fromTuple((xmlInfo("cscd_id"), xmlInfo("title"), xmlInfo("author_name"), xmlInfo("author_institute"), xmlInfo("journal"), xmlInfo("volume"), xmlInfo("year"), xmlInfo("page_string"), xmlInfo("issn"), xmlInfo("issue"), xmlInfo("cited_num"), xmlInfo("keywords"), xmlInfo("doi"), xmlInfo("abstract")))
                  flag = false
                }
                i = i + 1
              }
              row
            } else {
              //Row.fromSeq(null)
              //Row.fromSeq(Seq(1, 2, 3))
              null
            }
          } catch {
            case e:Throwable => println(e)
              null
          }

        }).toIterator
      }
      else {
        Iterator()
      }
    }).filter(f => f != null)
    println("---rdd count---")
    println(rdd.count())
    //val df = spark.createDataFrame(rdd, Article.getClass)
    val df = spark.createDataFrame(rdd, schema)
    //df.show()
    out.write(df)


  }


}
