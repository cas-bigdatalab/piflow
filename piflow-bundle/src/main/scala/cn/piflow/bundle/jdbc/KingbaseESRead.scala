package cn.piflow.bundle.jdbc

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession


class KingbaseESRead extends ConfigurableStop {

  val authorEmail: String = "3175989593@qq.com"
  val description: String = "Read data from KingbaseES database with KingbaseES jdbc driver"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var user:String = _
  var password:String = _
  var selectedContent:String = _
  var tableName:String = _
  var hint:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    var dbtable:String = ""

    // concat hint if exists
    if (hint == null || hint.trim.isEmpty) {
      dbtable = s"(select $selectedContent from $tableName) AS Temp"
    } else {
      dbtable = s"(select /*+ $hint */ $selectedContent from $tableName) AS Temp"
    }

    val jdbcDF = spark.read.format("jdbc")
      .option("url", url)
      .option("driver", "com.kingbase8.Driver")
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
    hint = MapUtil.get(map,"hint").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url of KingbaseES database")
      .defaultValue("jdbc:kingbase8://...:kingbase")
      .required(true)
      .example("jdbc:kingbase8://127.0.0.1:5432/dbname")
    descriptor = url :: descriptor

    val user=new PropertyDescriptor()
      .name("user")
      .displayName("User")
      .description("The user name of KingbaseES")
      .defaultValue("")
      .required(true)
      .example("user")
    descriptor = user :: descriptor

    val password=new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of KingbaseES")
      .defaultValue("")
      .required(true)
      .example("password")
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
    ImageUtil.getImage("icon/jdbc/KingbaseESRead.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }

}
