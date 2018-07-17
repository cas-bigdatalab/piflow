package cn.piflow.bundle.script

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, ScriptGroup, StopGroup}
import org.apache.spark.sql.{Row, SparkSession}
import org.apache.spark.sql.types.{StringType, StructField, StructType}

import sys.process._

class ShellExecutor extends ConfigurableStop{
  var shellPath: String = _
  var args: Array[String] = _
  var outputSchema: String = _


  override def setProperties(map: Map[String, Any]): Unit = {

    shellPath = MapUtil.get(map,"shellPath").asInstanceOf[String]
    //args = MapUtil.get(map,"args").asInstanceOf[Array[String]]
    outputSchema = MapUtil.get(map,"outputSchema").asInstanceOf[String]

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
    val result = shellPath !!
    val rawData = result.split("\n").toList

    var rowList = List[Row]()
    rawData.foreach( s => rowList = Row(s) :: rowList )

    val spark = pec.get[SparkSession]()

    val rdd = spark.sparkContext.parallelize(rowList)

    //Construct StructType
    /*val field = outputSchema.split(",")
    val structFieldArray : Array[StructField] = new Array[StructField](field.size)
    for(i <- 0 to field.size - 1){
      structFieldArray(i) = new StructField(field(i), StringType, nullable = true)
    }
    val schema : StructType = StructType(structFieldArray)*/
    val schema = StructType(List(new StructField("row", StringType, nullable = true)))

    println("")
    val df = spark.createDataFrame(rdd, schema)
    out.write(df)

  }
}
