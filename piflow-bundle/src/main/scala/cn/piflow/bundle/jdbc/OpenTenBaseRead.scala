package cn.piflow.bundle.jdbc

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession


class OpenTenBaseRead extends ConfigurableStop  {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Read data from OpenTenBase database with jdbc"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var user:String = _
  var password:String = _
  var selectedContent:String = _
  var tableName:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val dbtable = "( select " + selectedContent + " from " + tableName + " ) AS Temp"
    val jdbcDF = spark.read.format("jdbc")
      .option("url", url)
      .option("driver", "org.postgresql.Driver")
      .option("dbtable", dbtable)
      .option("user", user)
      .option("password",password)
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
    tableName= MapUtil.get(map,"tableName").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url of OpenTenBase database")
      .defaultValue("")
      .required(true)
      .example("jdbc:postgresql://127.0.0.1:30004/tbase")
    descriptor = url :: descriptor


    val user=new PropertyDescriptor()
      .name("user")
      .displayName("User")
      .description("The user name of OpenTenBase")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = user :: descriptor

    val password=new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of OpenTenBase")
      .defaultValue("")
      .required(true)
      .example("")
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
      .example("")
    descriptor = tableName :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/tbase.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }

}