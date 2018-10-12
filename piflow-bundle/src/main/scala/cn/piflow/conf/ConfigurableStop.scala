package cn.piflow.conf

import cn.piflow.Stop
import cn.piflow.conf.bean.PropertyDescriptor


abstract class ConfigurableStop extends Stop{

  val authorEmail : String
  val inportCount : Int
  val outportCount : Int
  val description : String


  def setProperties(map: Map[String, Any])

  def getPropertyDescriptor() : List[PropertyDescriptor]

  def getIcon() : Array[Byte]

  def getGroup() : List[String]

}
