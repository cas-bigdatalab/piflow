package cn.piflow.bundle.csv

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.apache.spark.sql.functions.monotonically_increasing_id

class FolderCsvParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val description: String = "Parsing of CSV folder"


  var FolderPath:String=_
  var delimiter: String = _
  var schema: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val session: SparkSession = pec.get[SparkSession]
    val context: SparkContext = session.sparkContext

    val StrRDD: RDD[String] = context.textFile(FolderPath)
    var num:Int=0
    var s:String=delimiter

    val rowRDD: RDD[Row] = StrRDD.map(line => {
      val seqSTR: Seq[String] = line.split(s).toSeq
      num=seqSTR.size
      val row = Row.fromSeq(seqSTR)
      row
    })

    val schameARR: Array[String] = schema.split(",")
    val fields: Array[StructField] = schameARR.map(d=>StructField(d.trim,StringType,nullable = true))

    val NewSchema: StructType = StructType(fields)
    val frame: DataFrame = session.createDataFrame(rowRDD,NewSchema)

    val Fdf = frame.filter(row=>{
      var bool: Boolean =true
      for(x<-(0 until num)){
        bool=row.get(x).equals(schameARR(x))
      }
      !bool
    }).toDF()

    Fdf.show(10)
    out.write(Fdf)

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    FolderPath = MapUtil.get(map,"csvPath").asInstanceOf[String]
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val FolderPath = new PropertyDescriptor().name("FolderPath").displayName("FolderPath").description("The path of csv Folder").defaultValue("").required(true)
    descriptor = FolderPath :: descriptor
    val delimiter = new PropertyDescriptor().name("delimiter").displayName("delimiter").description("The delimiter of csv file").defaultValue("").required(true)
    descriptor = delimiter :: descriptor
    val schema = new PropertyDescriptor().name("schema").displayName("schema").description("CSV string field description information, please use, split").defaultValue("").required(true)
    descriptor = schema :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("csv.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CsvGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
