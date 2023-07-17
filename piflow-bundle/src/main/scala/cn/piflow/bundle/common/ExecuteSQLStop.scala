package cn.piflow.bundle.common


import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.lib._
import cn.piflow.lib.io.{FileFormat, TextFile}
import org.apache.spark.sql.{DataFrame, SparkSession}

class ExecuteSQLStop extends ConfigurableStop{

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Create temporary view table to execute sql"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var sql: String = _
  var ViewName: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val inDF = in.read()
    inDF.createOrReplaceTempView(ViewName)

    val frame: DataFrame = spark.sql(sql)
    out.write(frame)
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    sql = MapUtil.get(map,"sql").asInstanceOf[String]
    ViewName = MapUtil.get(map,"viewName").asInstanceOf[String]

  }
  override def initialize(ctx: ProcessContext): Unit = {

  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val sql = new PropertyDescriptor().name("sql")
      .displayName("Sql")
      .description("Sql string")
      .defaultValue("")
      .required(true)
      .example("select * from temp")
    descriptor = sql :: descriptor

    val ViewName = new PropertyDescriptor()
      .name("viewName")
      .displayName("ViewName")
      .description("Name of the temporary view table")
      .defaultValue("temp")
      .required(true)
      .example("temp")

    descriptor = ViewName :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/ExecuteSqlStop.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }



}



