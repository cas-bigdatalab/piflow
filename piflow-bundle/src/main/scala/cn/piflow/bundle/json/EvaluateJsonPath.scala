package cn.piflow.bundle.json

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}

class EvaluateJsonPath extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val description: String = "Parsing of multiple JSON files"


  var jsonPathes: String = _
  var tag : String = _



  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val jsonPathARR: Array[String] = jsonPathes.split(";")

    val jsonDF = spark.read.option("multiline","true").json(jsonPathARR(0))
    var FinalDF: DataFrame = jsonDF.select(tag)

   if(jsonPathARR.length>1){
     for(x<-(1 until jsonPathARR.length)){
       var jDF: DataFrame = spark.read.option("multiline","true").json(jsonPathARR(x)).select(tag)
       val ff: DataFrame = FinalDF.union(jDF).toDF()
       FinalDF=ff
     }
   }


    out.write(jsonDF)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    jsonPathes = MapUtil.get(map,"jsonPathes").asInstanceOf[String]
    tag = MapUtil.get(map,"tag").asInstanceOf[String]
  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val jsonPathes = new PropertyDescriptor().name("jsonPathes").displayName("jsonPathes").description("The path of the json file,the delimiter is ;").defaultValue("").required(true)
    val tag=new PropertyDescriptor().name("tag").displayName("tag").description("The tag you want to parse").defaultValue("").required(true)
    descriptor = jsonPathes :: descriptor
    descriptor = tag :: descriptor
    descriptor
  }
  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("json.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JsonGroup.toString)
  }
  override def initialize(ctx: ProcessContext): Unit = {

  }


}
