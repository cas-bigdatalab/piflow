package cn.piflow.bundle.oceanbase

import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import org.apache.spark.sql.SparkSession


class OceanBaseRead extends ConfigurableStop{
  override val authorEmail: String = "llei@cnic.com"
  override val description: String = "Read data from OceanBase"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var driver :String = _
  var url : String=_
  var user :String = _
  var password :String = _
  var sql:String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val dbtable = "( "  + sql + ") AS Temp"
    val jdbcDF = spark.read.format("jdbc")
      .option("url", url)
      .option("driver", driver)
      .option("dbtable", dbtable)
      .option("user", user)
      .option("password",password)
      .load()

    out.write(jdbcDF)

  }
  override def setProperties(map: Map[String, Any]): Unit = {
    driver = MapUtil.get(map,key="driver").asInstanceOf[String]
    url = MapUtil.get(map,key="url").asInstanceOf[String]
    user = MapUtil.get(map,key="user").asInstanceOf[String]
    password = MapUtil.get(map,key="password").asInstanceOf[String]
    sql = MapUtil.get(map,key="sql").asInstanceOf[String]


  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val driver=new PropertyDescriptor()
      .name("driver")
      .displayName("Driver")
      .description("The Driver of tidb database")
      .defaultValue("com.mysql.jdbc.Driver")
      .required(true)
      .example("com.mysql.jdbc.Driver")
    descriptor = driver :: descriptor

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url, for example jdbc:mysql://127.0.0.1:2881/dbname")
      .defaultValue("")
      .required(true)
      .example("jdbc:mysql://127.0.0.1:2881/mysql")
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

    val sql=new PropertyDescriptor()
      .name("sql")
      .displayName("Sql")
      .description("The sql sentence you want to execute")
      .defaultValue("")
      .required(true)
      .language(Language.Sql)
      .example("select * from test.user1")
    descriptor = sql :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/OceanBaseRead.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
