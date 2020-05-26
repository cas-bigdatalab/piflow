package cn.piflow.bundle.csv

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

class CsvStringParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  override val description: String = "Parse csv string"


  var string:String=_
  var delimiter: String = _
  var schema: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val session: SparkSession = pec.get[SparkSession]
    val context: SparkContext = session.sparkContext

    val arrStr: Array[String] = string.split("\n").map(x => x.trim)

    var num:Int=0
    val listROW: List[Row] = arrStr.map(line => {
      val seqSTR: Seq[String] = line.split(delimiter).map(x=>x.trim).toSeq
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
    out.write(Fdf)
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    string = MapUtil.get(map,"string").asInstanceOf[String]
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val string = new PropertyDescriptor()
      .name("string")
      .displayName("String")
      .defaultValue("")
      .required(true)
      .example("1,zs\n2,ls\n3,ww")
    descriptor = string :: descriptor

    val delimiter = new PropertyDescriptor()
      .name("delimiter")
      .displayName("Delimiter")
      .description("The delimiter of CSV string")
      .defaultValue("")
      .required(true)
      .example(",")
    descriptor = delimiter :: descriptor

    val schema = new PropertyDescriptor()
      .name("schema")
      .displayName("Schema")
      .description("The schema of CSV string")
      .defaultValue("")
      .required(false)
      .example("")
    descriptor = schema :: descriptor

    descriptor

  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/csv/CsvStringParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CsvGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
