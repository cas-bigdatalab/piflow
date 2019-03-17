package cn.piflow.bundle.json

import cn.piflow.bundle.util.JsonUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql
import org.apache.spark.sql.{DataFrame, SparkSession}

import scala.util.control.Breaks.{break, breakable}

class MultiFolderJsonParser extends ConfigurableStop{
  val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  val description: String = "Analysis of multiple JSON folders"

  var jsonPathes: String = _
  var tag : String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val ss = pec.get[SparkSession]()

    val arrPath: Array[String] = jsonPathes.split(";")

    var index: Int = 0
    breakable {
      for (i <- 0 until arrPath.length) {
        if (ss.read.json(arrPath(i)).count() != 0) {
          index = i
          break
        }
      }
    }

    var FinalDF = ss.read.option("multiline","true").json(arrPath(index))

    for(d <- index+1 until(arrPath.length)){
      if(ss.read.json(arrPath(d)).count()!=0){
        val df1: DataFrame = ss.read.option("multiline","true").json(arrPath(d))
        val df2: DataFrame = FinalDF.union(df1).toDF()
        FinalDF=df2
      }
    }

    if(tag.length>0){
      val writeDF: DataFrame = JsonUtil.ParserJsonDF(FinalDF,tag)
      FinalDF=writeDF
    }

    out.write(FinalDF)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    jsonPathes = MapUtil.get(map,"jsonPathes").asInstanceOf[String]
    tag = MapUtil.get(map,"tag").asInstanceOf[String]
  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val jsonPathes = new PropertyDescriptor().name("jsonPathes").displayName("jsonPathes").description("The path of the json folder,the delimiter is ;").defaultValue("").required(true)
    val tag = new PropertyDescriptor().name("tag").displayName("tag").description("The tag you want to parse,If you want to open an array field,you have to write it like this:links_name(MasterField_ChildField)").defaultValue("").required(false)
    descriptor = jsonPathes :: descriptor
    descriptor = tag :: descriptor
    descriptor
  }
  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/json/MultiFolderJsonParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JsonGroup.toString)
  }
  override def initialize(ctx: ProcessContext): Unit = {

  }


}
