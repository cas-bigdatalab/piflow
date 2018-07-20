package cn.piflow.bundle.script

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, ScriptGroup, StopGroup}
import org.apache.spark.sql.{Row, SparkSession}
import org.apache.spark.sql.types.{StringType, StructField, StructType}

import scala.beans.BeanProperty
import sys.process._

class ShellExecutor extends ConfigurableStop{

  val inportCount: Int = 0
  val outportCount: Int = 1

  var shellPath: String = _
  var args: String = _
  var outputSchema: String = _


  override def setProperties(map: Map[String, Any]): Unit = {

    shellPath = MapUtil.get(map,"shellPath").asInstanceOf[String]
    args = MapUtil.get(map,"args").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/ShellExecutor.jpg")
  }

  override def getGroup(): StopGroup = {
    ScriptGroup
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
    df.show()

    out.write(df)
  }
}
