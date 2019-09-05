package cn.piflow.bundle.xml

import cn.piflow._
import cn.piflow.bundle.util.XmlToJson
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.{DataFrame, SparkSession}


class XmlParserWithJson extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Parse xml fields "
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var xmlColumn:String = _


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val inDf = in.read().select(xmlColumn)

    val rdd: RDD[String] = inDf.rdd.map(x => {
      XmlToJson.xmlParse(x.get(0).toString).replace("\n", "")
    })
    val xmlDF: DataFrame = spark.read.json(rdd)

    out.write(xmlDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    xmlColumn = MapUtil.get(map,"xmlColumn").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val xmlColumn = new PropertyDescriptor().name("xmlColumn").displayName("xmlColumn").description("the Column Contains XML String").defaultValue("").required(true)
    descriptor = xmlColumn :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/xml/XmlParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.XmlGroup.toString)
  }



}
