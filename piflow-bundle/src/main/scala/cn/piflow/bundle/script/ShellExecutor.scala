package cn.piflow.bundle.script

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import org.apache.spark.sql.{Row, SparkSession}
import org.apache.spark.sql.types.{StringType, StructField, StructType}

import scala.beans.BeanProperty
import sys.process._

class ShellExecutor extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Execute shell script."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var shellPath: String = _
  var args: String = _
  var outputSchema: String = _


  override def setProperties(map: Map[String, Any]): Unit = {

    shellPath = MapUtil.get(map,"shellPath").asInstanceOf[String]
    args = MapUtil.get(map,"args").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val shellPath = new PropertyDescriptor().name("shellPath").displayName("shellPath").description("The path of shell script").defaultValue("").required(true)
    val args = new PropertyDescriptor().name("args").displayName("args").description("The arguments of the shell script").defaultValue("").required(true)
    descriptor = shellPath :: descriptor
    descriptor = args :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/script/ShellExecutor.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ScriptGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val command = shellPath + " " + args
    val result =  command!!

    var rowList : List[Row] = List()
    val rawData = result.split("\n").toList
    rawData.foreach( s => rowList = Row(s) :: rowList )

    val spark = pec.get[SparkSession]()

    val rowsRdd = spark.sparkContext.parallelize(rowList)
    val schema = StructType(List(new StructField("row", StringType, nullable = true)))
    val df = spark.createDataFrame(rowsRdd,schema)
    //df.show()

    out.write(df)
  }
}
