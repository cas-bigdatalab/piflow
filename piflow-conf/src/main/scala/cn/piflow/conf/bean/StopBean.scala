package cn.piflow.conf.bean

import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.util.MapUtil

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
    //val stop = Class.forName(this.bundle).getConstructor(classOf[Map[String, String]]).newInstance(this.properties)
    val stop = Class.forName(this.bundle).newInstance()
    stop.asInstanceOf[ConfigurableStop].setProperties(this.properties)
    stop.asInstanceOf[ConfigurableStop]
  }

}

object StopBean  {

  def apply(map : Map[String, Any]): StopBean = {
    val stopBean = new StopBean()
    stopBean.init(map)
    stopBean
  }

}

