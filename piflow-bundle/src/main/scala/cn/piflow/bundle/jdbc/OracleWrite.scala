package cn.piflow.bundle.jdbc

import java.sql.{Connection, DriverManager, Statement}

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql._

class OracleWrite extends ConfigurableStop{

  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "Write data to oracle"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var user:String = _
  var password:String = _
  var table:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val session = pec.get[SparkSession]()
    val inDF: DataFrame = in.read()

    Class.forName("oracle.jdbc.driver.OracleDriver")
    val con: Connection = DriverManager.getConnection(url,user,password)
    val star: Statement = con.createStatement()

    val fileNames: Array[String] = inDF.columns
    var fileNameStr:String=""
    var createSQL:String="create table "+table+"("
    fileNames.foreach(name => {
      fileNameStr+=(","+name)
      createSQL+=(name+" varchar2(100),")
    })

    star.executeUpdate(createSQL.substring(0,createSQL.length-1)+")")


    inDF.collect().foreach(r => {
      var insertSQL:String="insert into "+table+"("+fileNameStr.substring(1)+") Values("
      var rowStr:String=""
      val rs: Array[String] = r.toString().substring(1, r.toString().length - 1).split(",")
      for(x <- rs){
        rowStr+=(",'"+x+"'")
      }
      insertSQL+=(rowStr.substring(1)+")")

      star.executeUpdate(insertSQL)
    })
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    table = MapUtil.get(map,"table").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url, for example jdbc:oracle:thin:@10.0.86.237:1521/newdb")
      .defaultValue("")
      .required(true)
      .example("jdbc:oracle:thin:@10.0.86.237:1521/newdb")
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

    val table=new PropertyDescriptor()
      .name("table")
      .displayName("table")
      .description("The table name")
      .defaultValue("")
      .required(true)
      .example("test")
    descriptor = table :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/OracleWrite.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }


}
