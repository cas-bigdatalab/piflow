package cn.piflow.bundle.script

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{CommonGroup, ConfigurableStop, ScriptGroup, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Row, SparkSession}

import scala.beans.BeanProperty

class DataFrameRowParser extends ConfigurableStop{

  val inportCount: Int = 1
  val outportCount: Int = 1

  var schema: String = _
  var separator: String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
    separator = MapUtil.get(map,"separator").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/DataFrameParse.jpg")
  }

  override def getGroup(): StopGroup = {
    ScriptGroup
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDF = in.read()

    //parse RDD
    val rdd = inDF.rdd.map(row => {
      val fieldArray = row.get(0).asInstanceOf[String].split(",")
      Row.fromSeq(fieldArray.toSeq)
    })

    //parse schema
    val field = schema.split(separator)
    val structFieldArray : Array[StructField] = new Array[StructField](field.size)
    for(i <- 0 to field.size - 1){
      structFieldArray(i) = new StructField(field(i),StringType, nullable = true)
    }
    val schemaStructType = StructType(structFieldArray)

    //create DataFrame
    val df = spark.createDataFrame(rdd,schemaStructType)
    df.show()
    out.write(df)
  }

}
