package cn.piflow.bundle.jdbc

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SaveMode

import java.util.Properties


class KingbaseESWrite extends ConfigurableStop{
  val authorEmail: String = "3175989593@qq.com"
  val description: String = "Write data to KingbaseES database with KingbaseES jdbc driver"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var user:String = _
  var password:String = _
  var dbtable:String = _
  var saveMode:String = _
  var batchSize:Int = _
  var hint:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val jdbcDF = in.read()
    val properties = new Properties()
    properties.put("user", user)
    properties.put("password", password)
    properties.put("driver", "com.kingbase8.Driver")
    properties.put("batchsize", batchSize.toString) // when as property for JDBC, it should be string

    if (hint != null && hint.trim.nonEmpty) {
      // concat hint at front of dbtable
      dbtable = s"/*+ $hint */ $dbtable"
    }

    jdbcDF.write
      .mode(SaveMode.valueOf(saveMode)).jdbc(url,dbtable,properties)
    out.write(jdbcDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    dbtable = MapUtil.get(map,"dbtable").asInstanceOf[String]
    saveMode = MapUtil.get(map,"saveMode").asInstanceOf[String]
    batchSize = Integer.parseInt(MapUtil.get(map, "batchSize").asInstanceOf[String])
    hint = MapUtil.get(map, "hint").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val saveModeOption = Set("Append", "Overwrite", "Ignore")

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url of KingbaseES database")
      .defaultValue("jdbc:kingbase8://...:5432/kingbase")
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
      .description("The password of openGauss")
      .defaultValue("")
      .required(true)
      .example("password")
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

    val batchSize = new PropertyDescriptor()
      .name("batchSize")
      .displayName("BatchSize")
      .description("The batch size for writing data to openGauss")
      .defaultValue("1000")
      .required(true)
      .example("1000")
    descriptor = batchSize :: descriptor

    val hint = new PropertyDescriptor()
      .name("hint")
      .displayName("Hint")
      .description("The hint for writing data to openGauss, default is append")
      .defaultValue("")
      .required(false)
      .example("")
    descriptor = hint :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/KingbaseESWrite.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }

}
