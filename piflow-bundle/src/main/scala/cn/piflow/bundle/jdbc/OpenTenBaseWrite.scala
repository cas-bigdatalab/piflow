package cn.piflow.bundle.jdbc

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.util.SciDataFrame
import org.apache.spark.sql.{SaveMode, SparkSession}

import java.util.Properties


class OpenTenBaseWrite extends ConfigurableStop{

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Write data into OpenTenBase database with jdbc"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var user:String = _
  var password:String = _
  var dbtable:String = _
  var saveMode:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val jdbcDF = in.read().getSparkDf
    val properties = new Properties()
    properties.put("user", user)
    properties.put("password", password)
    properties.put("driver", "org.postgresql.Driver")

    jdbcDF.write
      .mode(SaveMode.valueOf(saveMode)).jdbc(url,dbtable,properties)
    out.write(new SciDataFrame(jdbcDF))
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    dbtable = MapUtil.get(map,"dbtable").asInstanceOf[String]
    saveMode = MapUtil.get(map,"saveMode").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val saveModeOption = Set("Append", "Overwrite", "Ignore")

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

    val saveMode = new PropertyDescriptor()
      .name("saveMode")
      .displayName("SaveMode")
      .description("The save mode for table")
      .allowableValues(saveModeOption)
      .defaultValue("Append")
      .required(true)
      .example("Append")
    descriptor = saveMode :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/tbase.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }

}
