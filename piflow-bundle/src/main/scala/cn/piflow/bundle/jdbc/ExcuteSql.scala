package cn.piflow.bundle.jdbc

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

import java.sql.{Connection, DriverManager, ResultSet}


class ExcuteSql extends ConfigurableStop {

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Read data from mysql database with jdbc"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url: String = _
  var driver: String = _
  var user: String = _
  var password: String = _
  var sql: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val dbtable = sql
    val jdbcDF = spark.sql("show databases")
    Class.forName(driver)
    val conn: Connection = DriverManager.getConnection(url, user, password)
    val statement = conn.createStatement()
    statement.execute(dbtable)
    conn.close()
    statement.close()

    out.write(jdbcDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {

    url = MapUtil.get(map, "url").asInstanceOf[String]
    driver = MapUtil.get(map, "driver").asInstanceOf[String]
    user = MapUtil.get(map, "user").asInstanceOf[String]
    password = MapUtil.get(map, "password").asInstanceOf[String]
    sql = MapUtil.get(map, "sql").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()

    val url = new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url of mysql database")
      .defaultValue("")
      .required(true)
      .example("jdbc:mysql://127.0.0.1:3306/dbname")
    descriptor = url :: descriptor

    val driver = new PropertyDescriptor()
      .name("driver")
      .displayName("Driver")
      .description("The Driver of mysql database")
      .defaultValue("com.mysql.jdbc.Driver")
      .required(true)
      .example("com.mysql.jdbc.Driver")
    descriptor = driver :: descriptor

    val user = new PropertyDescriptor()
      .name("user")
      .displayName("User")
      .description("The user name of mysql database")
      .defaultValue("")
      .required(true)
      .example("root")
    descriptor = user :: descriptor

    val password = new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of mysql database")
      .defaultValue("")
      .required(true)
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
      .example("select * from test.user1")
    descriptor = sql :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/MysqlRead.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }


}
