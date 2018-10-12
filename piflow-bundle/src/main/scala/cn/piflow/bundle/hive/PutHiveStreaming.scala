package cn.piflow.bundle.hive

import cn.piflow._
import cn.piflow.conf.{ConfigurableStop, HiveGroup, StopGroup, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

import scala.beans.BeanProperty

class PutHiveStreaming extends ConfigurableStop {

  val authorEmail: String = "xjzhu@cnic.cn"
  val inportCount: Int = 1
  val outportCount: Int = 0

  var database:String = _
  var table:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDF = in.read()
    inDF.show()

    val dfTempTable = table + "_temp"
    inDF.createOrReplaceTempView(dfTempTable)
    spark.sql("insert into " + database + "." + table +  " select * from " + dfTempTable)
    //out.write(studentDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    database = MapUtil.get(map,"database").asInstanceOf[String]
    table = MapUtil.get(map,"table").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val database=new PropertyDescriptor().name("database").displayName("DataBase").description("The database name").defaultValue("").required(true)
    val table = new PropertyDescriptor().name("table").displayName("Table").description("The table name").defaultValue("").required(true)
    descriptor = database :: descriptor
    descriptor = table :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/selectHiveQL.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.HiveGroup.toString)
  }


}
