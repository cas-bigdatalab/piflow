package cn.piflow.bundle.xml

import cn.piflow._
import cn.piflow.conf.{ConfigurableStop, StopGroup, XmlGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.codehaus.jackson.map.ext.CoreXMLSerializers.XMLGregorianCalendarSerializer

import scala.beans.BeanProperty

class XmlSave extends ConfigurableStop{

  val inportCount: Int = 1
  val outportCount: Int = 0

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

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): StopGroup = {
    XmlGroup
  }

}
