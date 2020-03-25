package cn.piflow.bundle.csv

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

class FolderCsvParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(Port.NonePort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)
  override val description: String = "Parse csv folder"

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

    out.write(Fdf)

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    FolderPath = MapUtil.get(map,"csvPath").asInstanceOf[String]
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val FolderPath = new PropertyDescriptor()
      .name("FolderPath")
      .displayName("FolderPath")
      .description("The path of csv Folder")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = FolderPath :: descriptor

    val delimiter = new PropertyDescriptor()
      .name("delimiter")
      .displayName("delimiter")
      .description("The delimiter of csv file")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = delimiter :: descriptor

    val schema = new PropertyDescriptor()
      .name("schema")
      .displayName("schema")
      .description("The schema of CSV string")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = schema :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/csv/FolderCsvParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CsvGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
