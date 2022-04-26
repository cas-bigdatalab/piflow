package cn.piflow.conf

import cn.piflow.Stop
import cn.piflow.conf.bean.PropertyDescriptor



abstract class ConfigurableStop extends Stop{

  val authorEmail : String
  val description : String

  val inportList : List[String] //= List(PortEnum.DefaultPort.toString)
  val outportList : List[String] //= List(PortEnum.DefaultPort.toString)

  //Have customized properties or not
  val isCustomized = false
  val customizedAllowKey = List[String]()
  val customizedAllowValue = List[String]()

  var customizedProperties : Map[String, String] = null

  val isDataSource = false

  def setProperties(map: Map[String, Any])

  def getPropertyDescriptor() : List[PropertyDescriptor]

  def getIcon() : Array[Byte]

  def getGroup() : List[String]

  def setCustomizedProperties( customizedProperties : Map[String, String]) = {
    this.customizedProperties = customizedProperties
  }

  def getCustomized() : Boolean = {
    this.isCustomized
  }

  def getIsDataSource() : Boolean = {
    this.isDataSource
  }

}
