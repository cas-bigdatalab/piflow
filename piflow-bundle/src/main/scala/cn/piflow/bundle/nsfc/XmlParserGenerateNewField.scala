package cn.piflow.bundle.nsfc

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

import scala.xml.{Elem, NodeSeq, XML}

class XmlParserGenerateNewField extends ConfigurableStop {

  val authorEmail: String = "songdongze@cnic.cn"
  val description: String = "parse xml string from a hive field, and generate a new field from a xml tag"
  val inportList: List[String] = List(PortEnum.AnyPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var decoderField: String = _
  var tagXPath: String = _
  var newField: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val sqlContext=spark.sqlContext
    val dfOld = in.read()
    dfOld.createOrReplaceTempView("thesis")
    val s1: Array[String] = tagXPath.split("/");
    sqlContext.udf.register("regexPro",(str:String)=>{
      val xml: Elem = XML.loadString(str)
      var type_id: NodeSeq = xml
      for (i <- 2 until s1.length) {
        type_id = type_id \ s1(i)
      }
      type_id.text
    })
    val sqlText:String="select *, regexPro(" + decoderField + ") as " + newField + " from thesis"

    val dfNew=sqlContext.sql(sqlText)
    dfNew.show()
    out.write(dfNew)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    decoderField = MapUtil.get(map,"decoderField").asInstanceOf[String]
    tagXPath = MapUtil.get(map,"tagXPath").asInstanceOf[String]
    newField = MapUtil.get(map,"newField").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val decoderField = new PropertyDescriptor().name("decoderField").displayName("decoder field").description("decoder field").defaultValue("").required(true)
    val tagXPath = new PropertyDescriptor().name("tagXPath").displayName("xml tag XPath").description("the tag you want to parse in xml file, XPath").defaultValue("").required(true)
    val newField = new PropertyDescriptor().name("newField").displayName("new Field name").description("generate a new field from tag").defaultValue("").required(true)
    descriptor = decoderField :: descriptor
    descriptor = tagXPath :: descriptor
    descriptor = newField :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/xml/XmlParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.XmlGroup.toString)
  }

}
