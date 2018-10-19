package cn.piflow.bundle.xml

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.codehaus.jackson.map.ext.CoreXMLSerializers.XMLGregorianCalendarSerializer

import scala.beans.BeanProperty

class XmlSave extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Save data to xml file."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)

  var xmlSavePath:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val xmlDF = in.read()
    xmlDF.show()

    xmlDF.write.format("xml").save(xmlSavePath)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    xmlSavePath = MapUtil.get(map,"xmlSavePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val xmlSavePath = new PropertyDescriptor().name("xmlSavePath").displayName("xmlSavePath").description("the sva path of xml file").defaultValue("").required(true)
    descriptor = xmlSavePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("xml.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.XmlGroup.toString)
  }

}
