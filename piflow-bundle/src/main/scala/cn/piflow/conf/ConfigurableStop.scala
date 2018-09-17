package cn.piflow.conf

import cn.piflow.Stop
import cn.piflow.conf.bean.PropertyDescriptor


trait ConfigurableStop extends Stop{

  val authorEmail : String
  val inportCount : Int
  val outportCount : Int


  def setProperties(map: Map[String, Any])

  def getPropertyDescriptor() : List[PropertyDescriptor]

  def getIcon() : Array[Byte]

  def getGroup() : StopGroup

}
