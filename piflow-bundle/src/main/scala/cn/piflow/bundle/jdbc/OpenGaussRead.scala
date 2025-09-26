package cn.piflow.bundle.jdbc

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession


class OpenGaussRead extends ConfigurableStop {

  val authorEmail: String = "3175989593@qq.com"
  val description: String = "Read data from openGauss database with jdbc driver"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var user:String = _
  var password:String = _
  var selectedContent:String = _
  var tableName:String = _
  var queryDop:Int = _
  var hint:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    var totalHint: String = "" // concat the hint, including query_dop and other custom hints

    if (hint == null || hint.trim.isEmpty) {
      totalHint = s"/*+ SET(query_dop $queryDop) */"
    } else {
      totalHint = s"/*+ SET(query_dop $queryDop $hint )*/"
    }

    // add hint in the sql
    val dbtable = s"(select $totalHint $selectedContent from $tableName ) AS Temp"

    val jdbcDF = spark.read.format("jdbc")
      .option("url", url)
      .option("driver", "org.postgresql.Driver") // openGauss can also use the postgresql driver
      .option("dbtable", dbtable)
      .option("user", user)
      .option("password", password)
      .load()

    out.write(jdbcDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {

    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    selectedContent= MapUtil.get(map,"selectedContent").asInstanceOf[String]
    tableName = MapUtil.get(map,"tableName").asInstanceOf[String]
    queryDop = Integer.parseInt(MapUtil.get(map,key="queryDop").toString)
    hint = MapUtil.get(map,"hint").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url of openGauss database")
      .defaultValue("jdbc:postgresql://...:5432/postgres") // when use postgresql driver, the jdbc url is postgresql format
      .required(true)
      .example("jdbc:postgresql://127.0.0.1:5432/dbname")
    descriptor = url :: descriptor

    val user=new PropertyDescriptor()
      .name("user")
      .displayName("User")
      .description("The user name of openGauss")
      .defaultValue("")
      .required(true)
      .example("opengauss")
    descriptor = user :: descriptor

    val password=new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of openGauss")
      .defaultValue("")
      .required(true)
      .example("openGauss1234@")
      .sensitive(true)
    descriptor = password :: descriptor

    val selectedContent =new PropertyDescriptor()
      .name("selectedContent")
      .displayName("SelectedContent")
      .description("The content you selected to read in the DBTable")
      .defaultValue("*")
      .required(true)
      .example("*")
    descriptor = selectedContent :: descriptor

    val tableName =new PropertyDescriptor()
      .name("tableName")
      .displayName("TableName")
      .description("The table you want to read")
      .defaultValue("")
      .required(true)
      .example("test")
    descriptor = tableName :: descriptor

    val queryDop = new PropertyDescriptor()
      .name("queryDop")
      .displayName("QueryDop")
      .description("The degree of parallelism for the query, default is 1")
      .defaultValue("1")
      .required(false)
      .example("1")
    descriptor = queryDop :: descriptor

    val hint = new PropertyDescriptor()
      .name("hint")
      .displayName("Hint")
      .description("The hint for the query, default is empty, multiple hints can be separated by space")
      .defaultValue("")
      .required(false)
      .example("")
    descriptor = hint :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/openGaussRead.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }
}
