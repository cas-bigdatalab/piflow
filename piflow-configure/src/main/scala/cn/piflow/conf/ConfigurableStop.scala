package cn.piflow.conf

import cn.piflow.Stop
import cn.piflow.conf.bean.PropertyDescriptor



abstract class ConfigurableStop extends Stop{

  val authorEmail : String
  val description : String
  //PortEnum.AnyPort: any port; PortEnum.DefaultPort: default port
  //null: no port; userdefinePort: port1, port2...
  val inportList : List[String] //= List(PortEnum.DefaultPort.toString)
  val outportList : List[String] //= List(PortEnum.DefaultPort.toString)

  val isCustomized = false

  var customizedProperties : Map[String, String] = null

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

}
