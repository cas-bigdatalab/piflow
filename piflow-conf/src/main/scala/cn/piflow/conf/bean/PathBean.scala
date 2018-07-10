package cn.piflow.conf.bean

import cn.piflow.conf.util.MapUtil

class PathBean {
  var from : String = _
  var outport : String = _
  var inport : String = _
  var to : String = _

  def init(from:String, outport: String, inport : String, to:String)= {
    this.from = from
    this.outport = outport
    this.inport = inport
    this.to = to
  }
  def init(map:Map[String,Any])= {
    this.from = MapUtil.get(map,"from").asInstanceOf[String]
    this.outport = MapUtil.get(map,"outport").asInstanceOf[String]
    this.inport = MapUtil.get(map,"inport").asInstanceOf[String]
    this.to = MapUtil.get(map,"to").asInstanceOf[String]
  }

}

object PathBean{
  def apply(map : Map[String, Any]): PathBean = {
    val pathBean = new PathBean()
    pathBean.init(map)
    pathBean
  }
}

