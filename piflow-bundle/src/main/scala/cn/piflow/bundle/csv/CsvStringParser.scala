package cn.piflow.bundle.csv

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.apache.spark.sql.functions.monotonically_increasing_id

class CsvStringParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val description: String = ""


  var Str:String=_
  var delimiter: String = _
  var schema: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val session: SparkSession = pec.get[SparkSession]
    val context: SparkContext = session.sparkContext

    val arrStr: Array[String] = Str.split("\n")

    var num:Int=0
    val listROW: List[Row] = arrStr.map(line => {
      val seqSTR: Seq[String] = line.split(delimiter).toSeq
      num=seqSTR.size
      val row = Row.fromSeq(seqSTR)
      row
    }).toList
    val rowRDD: RDD[Row] = context.makeRDD(listROW)

    var Fdf: DataFrame =null
    if(schema.length==0){
      (0 until num).foreach(x=>{
        schema+=("_"+x+",")
      })
    }
    val fields: Array[StructField] = schema.split(",").map(d=>StructField(d.trim,StringType,nullable = true))
    val NewSchema: StructType = StructType(fields)
    Fdf = session.createDataFrame(rowRDD,NewSchema)

    Fdf.show(10)
    out.write(Fdf)
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    Str = MapUtil.get(map,"Str").asInstanceOf[String]
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val Str = new PropertyDescriptor().name("Str").displayName("Str").defaultValue("").required(true)
    descriptor = Str :: descriptor
    val delimiter = new PropertyDescriptor().name("delimiter").displayName("delimiter").description("The delimiter of the String").defaultValue("").required(true)
    descriptor = delimiter :: descriptor
    val schema = new PropertyDescriptor().name("schema").displayName("schema").description("The schema of the String,The delimiter is ,").defaultValue("").required(false)
    descriptor = schema :: descriptor
    descriptor

  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("csv.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.CsvGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
