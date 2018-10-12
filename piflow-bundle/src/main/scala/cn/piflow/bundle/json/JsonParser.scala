package cn.piflow.bundle.json

import cn.piflow._
import cn.piflow.conf.{ConfigurableStop, JsonGroup, StopGroup, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

import scala.beans.BeanProperty

class JsonParser extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val inportCount: Int = 1
  val outportCount: Int = 1

  var jsonPath: String = _
  var tag : String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    val jsonDF = spark.read.option("multiline","true").json(jsonPath)
    val jsonDFNew = jsonDF.select(tag)
    jsonDFNew.printSchema()
    jsonDFNew.show(10)
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
    val tag=new PropertyDescriptor().name("tag").displayName("tag").description("The tag you want to parse").defaultValue("").required(true)
    descriptor = jsonPath :: descriptor
    descriptor = tag :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/selectHiveQL.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.JsonGroup.toString)
  }

}

