package cn.piflow.bundle.xml

import cn.piflow._
import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil

class XmlSave extends ConfigurableStop{

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
}
