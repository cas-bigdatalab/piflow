package cn.piflow.bundle.xml

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.codehaus.jackson.map.ext.CoreXMLSerializers.XMLGregorianCalendarSerializer

import scala.beans.BeanProperty

class XmlSave extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Save data to xml file"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var xmlSavePath:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val xmlDF = in.read()

    xmlDF.write.format("xml").save(xmlSavePath)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    xmlSavePath = MapUtil.get(map,"xmlSavePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val xmlSavePath = new PropertyDescriptor()
      .name("xmlSavePath")
      .displayName("XmlSavePath")
      .description("xml file save path")
      .defaultValue("")
      .required(true)
        .example("hdfs://192.168.3.138:8020/work/test/test.xml")
    descriptor = xmlSavePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/xml/XmlSave.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.XmlGroup)
  }

}
