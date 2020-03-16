package cn.piflow.bundle.json

import cn.piflow._
import cn.piflow.bundle.util.JsonUtil
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}

import scala.beans.BeanProperty

class JsonParser extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Parse json file"
  val inportList: List[String] = List(Port.NonePort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)

  var jsonPath: String = _
  var tag : String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    var jsonDF = spark.read.json(jsonPath)

    if(tag.length>0){
      val writeDF: DataFrame = JsonUtil.ParserJsonDF(jsonDF,tag)
      jsonDF=writeDF
    }

    //jsonDF.printSchema()
    //jsonDF.show(10)
    out.write(jsonDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    jsonPath = MapUtil.get(map,"jsonPath").asInstanceOf[String]
    tag = MapUtil.get(map,"tag").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val jsonPath = new PropertyDescriptor().name("jsonPath").displayName("jsonPath").description("The path of the json file").defaultValue("").required(true)
    val tag = new PropertyDescriptor().name("tag").displayName("tag").description("The tag you want to parse,If you want to open an array field,you have to write it like this:links_name(MasterField_ChildField)").defaultValue("").required(false)
    descriptor = jsonPath :: descriptor
    descriptor = tag :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/json/jsonParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JsonGroup.toString)
  }

}

