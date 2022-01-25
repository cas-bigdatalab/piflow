package cn.piflow.bundle.clickhouse

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SaveMode}

import java.util.Properties

class ClickhouseWrite extends ConfigurableStop{

  val authorEmail: String = "songdongze@cnic.cn"
  val description: String = "Write Data to Clickhouse Database"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var driver:String = _
  var user:String = _
  var password:String = _
  var dbtable:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val jdbcDF: DataFrame = in.read()
    val properties: Properties = new Properties()
    properties.put("driver", driver)
    if (user != null && user.nonEmpty) {
      properties.put("user", user)
      properties.put("password", password)
    }
    val options: Map[String, String] = Map[String,String] (
      "batchsize" -> "10000",
      "isolationLevel" -> "NONE",
      "numPartitions" -> "1"
    )
    jdbcDF.write.mode(SaveMode.Append).options(options).jdbc(url, dbtable, properties)
    out.write(jdbcDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    driver = MapUtil.get(map,"driver").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    dbtable = MapUtil.get(map,"dbtable").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url = new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Connection Url of Clickhouse Database")
      .defaultValue("jdbc:clickhouse://127.0.0.1:8123/default")
      .required(true)
      .example("jdbc:clickhouse://127.0.0.1:8123/default")
    descriptor = url :: descriptor

    val driver = new PropertyDescriptor()
      .name("driver")
      .displayName("Driver")
      .description("The JDBC Driver of Clickhouse Database")
      .defaultValue("ru.yandex.clickhouse.ClickHouseDriver")
      .required(true)
      .example("ru.yandex.clickhouse.ClickHouseDriver")
    descriptor = driver :: descriptor

    val user = new PropertyDescriptor()
      .name("user")
      .displayName("User")
      .description("The User of Clickhouse Database")
      .defaultValue("")
      .required(false)
      .example("default")
    descriptor = user :: descriptor

    val password = new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The Password of Clickhouse Database")
      .defaultValue("")
      .required(false)
      .example("")
      .sensitive(true)
    descriptor = password :: descriptor

    val dbtable = new PropertyDescriptor()
      .name("dbtable")
      .displayName("DBTable")
      .description("The Table you want to Write")
      .defaultValue("")
      .required(true)
      .example("test")
    descriptor = dbtable :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/ClickhouseWrite.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }


}
