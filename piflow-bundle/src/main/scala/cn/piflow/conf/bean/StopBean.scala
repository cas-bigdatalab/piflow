package cn.piflow.conf.bean

import java.lang.ClassNotFoundException

import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.util.{ClassUtil, MapUtil}

class StopBean {
  var uuid : String = _
  var name : String = _
  var bundle : String = _
  var properties : Map[String, String] = _

  def init(map:Map[String,Any]) = {
    this.uuid = MapUtil.get(map,"uuid").asInstanceOf[String]
    this.name = MapUtil.get(map,"name").asInstanceOf[String]
    this.bundle = MapUtil.get(map,"bundle").asInstanceOf[String]
    this.properties = MapUtil.get(map, "properties").asInstanceOf[Map[String, String]]
  }

  def constructStop() : ConfigurableStop = {

    try{
      val stop = ClassUtil.findConfigurableStop(this.bundle)
      stop.setProperties(this.properties)
      stop
    }catch {
      case ex : Exception => throw ex
    }
  }

}

object StopBean  {

  def apply(map : Map[String, Any]): StopBean = {
    val stopBean = new StopBean()
    stopBean.init(map)
    stopBean
  }

}

