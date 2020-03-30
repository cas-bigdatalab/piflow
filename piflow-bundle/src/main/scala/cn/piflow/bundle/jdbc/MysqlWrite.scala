package cn.piflow.bundle.jdbc

import java.util.Properties

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{SaveMode, SparkSession}

import scala.beans.BeanProperty

class MysqlWrite extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Write data to mysql database with jdbc"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.NonePort)

  var url:String = _
  var user:String = _
  var password:String = _
  var dbtable:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val jdbcDF = in.read()
    val properties = new Properties()
    properties.put("user", user)
    properties.put("password", password)
    jdbcDF.write.mode(SaveMode.Append).jdbc(url,dbtable,properties)
    out.write(jdbcDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    dbtable = MapUtil.get(map,"dbtable").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url, for example jdbc:mysql://127.0.0.1/dbname")
      .defaultValue("")
      .required(true)
      .example("jdbc:mysql://127.0.0.1/dbname")
    descriptor = url :: descriptor

    val user=new PropertyDescriptor()
      .name("user")
      .displayName("User")
      .description("The user name of database")
      .defaultValue("")
      .required(true)
      .example("root")
    descriptor = user :: descriptor

    val password=new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of database")
      .defaultValue("")
      .required(true)
      .example("123456")
      .sensitive(true)
    descriptor = password :: descriptor

    val dbtable=new PropertyDescriptor()
      .name("dbtable")
      .displayName("DBTable")
      .description("The table you want to write")
      .defaultValue("")
      .required(true)
      .example("test")
    descriptor = dbtable :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/jdbcWrite.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }


}
