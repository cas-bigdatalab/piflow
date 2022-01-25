package cn.piflow.bundle.clickhouse

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, SparkSession}

class ClickhouseRead extends ConfigurableStop  {

  val authorEmail: String = "songdongze@cnic.cn"
  val description: String = "Read Data from Clickhouse Database with using JDBC"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var driver:String = _
  var user:String = _
  var password:String = _
  var sql:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark: SparkSession = pec.get[SparkSession]()
    val dbtable: String =  "( "  + sql + ") temp"
    var options: Map[String, String] = Map[String, String](
      "url" -> url,
      "driver" -> driver,
      "dbtable" -> dbtable
    )
    if (user != null && user.nonEmpty) {
      options += ("user" -> user)
      options += ("password" -> password)
    }

    val jdbcDF: DataFrame = spark.read.format("jdbc")
      .options(options)
      .load()
    jdbcDF.show()
    out.write(jdbcDF)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {

    url = MapUtil.get(map,"url").asInstanceOf[String]
    driver = MapUtil.get(map, "driver").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    sql = MapUtil.get(map,"sql").asInstanceOf[String]
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
      .example("12345")
      .sensitive(true)
    descriptor = password :: descriptor

    val sql = new PropertyDescriptor()
      .name("sql")
      .displayName("Sql")
      .description("The sql sentence you want to execute")
      .defaultValue("")
      .required(true)
      .language(Language.Sql)
      .example("select * from default.test")
    descriptor = sql :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/ClickhouseRead.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }

}
