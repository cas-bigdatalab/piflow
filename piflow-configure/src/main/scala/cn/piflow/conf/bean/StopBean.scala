package cn.piflow.conf.bean

import java.lang.ClassNotFoundException

import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.util.{ClassUtil, MapUtil}

import scala.collection.mutable

class StopBean {
  var flowName : String = _
  var uuid : String = _
  var name : String = _
  var bundle : String = _
  var properties : Map[String, String] = _
  var customizedProperties : Map[String, String] = _

  def init(flowName : String, map:Map[String,Any]) = {
    this.flowName = flowName
    this.uuid = MapUtil.get(map,"uuid").asInstanceOf[String]
    this.name = MapUtil.get(map,"name").asInstanceOf[String]
    this.bundle = MapUtil.get(map,"bundle").asInstanceOf[String]
    this.properties = MapUtil.get(map, "properties").asInstanceOf[Map[String, String]]
    if(map.contains("customizedProperties")){
      this.customizedProperties  = MapUtil.get(map, "customizedProperties").asInstanceOf[Map[String, String]]
    }else{
      this.customizedProperties = Map[String, String]()
    }

  }

  def constructStop() : ConfigurableStop = {

    try{
      println("Construct stop: " + this.bundle + "!!!!!!!!!!!!!!!!!!!!!")
      val stop = ClassUtil.findConfigurableStop(this.bundle)
      println("Construct stop: " + stop + "!!!!!!!!!!!!!!!!!!!!!")

      println("properties is " + this.properties + "!!!!!!!!!!!!!!!")
      stop.asInstanceOf[ConfigurableStop].setProperties(this.properties)

      stop.setCustomizedProperties(this.customizedProperties)

      stop
    }catch {
      case ex : Exception => throw ex
    }
  }

}

object StopBean  {

  def apply(flowName : String, map : Map[String, Any]): StopBean = {
    val stopBean = new StopBean()
    stopBean.init(flowName, map)
    stopBean
  }

}

