package cn.piflow.bundle.csv

import cn.piflow._
import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, SparkSession}


class CSVParser extends ConfigurableStop{

  var csvPath: String = _
  var header: Boolean = _
  var delimiter: String = _
  var schema: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    var csvDF:DataFrame = null
    if (header){
      csvDF = spark.read
        .option("header",header)
        .option("inferSchema","true")
        .option("delimiter",delimiter)
        /*.schema(schema)*/
        .csv(csvPath)


    }else{

      val field = schema.split(",")
      val structFieldArray : Array[StructField] = new Array[StructField](field.size)
      for(i <- 0 to field.size - 1){
        structFieldArray(i) = new StructField(field(i), StringType, nullable = true)
      }
      val schemaStructType = StructType(structFieldArray)

      csvDF = spark.read
        .option("header",header)
        .option("inferSchema","false")
        .option("delimiter",delimiter)
        .schema(schemaStructType)
        .csv(csvPath)
    }

    csvDF.show(10)
    out.write(csvDF)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    csvPath = MapUtil.get(map,"csvPath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String].toBoolean
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???
}

