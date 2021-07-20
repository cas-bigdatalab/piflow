package cn.piflow.conf.bean

import cn.piflow.util.MapUtil

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */
class DataCenterConditionBean {

  var after : List[Entry] = List[Entry]()
  var outport : String = _
  var inport : String = _
  var entry : Entry = _

  def init(map:Map[String,Any])= {
    val afterMap = MapUtil.get(map,"after").asInstanceOf[Map[String, String]]
    this.after = Entry(afterMap) +: this.after

    this.outport = MapUtil.get(map,"outport").asInstanceOf[String]

    this.inport = MapUtil.get(map,"inport").asInstanceOf[String]

    val entryMap = MapUtil.get(map,"entry").asInstanceOf[Map[String, String]]
    this.entry = Entry(entryMap)
  }
}

object DataCenterConditionBean{

  def apply(map : Map[String, Any]): DataCenterConditionBean = {
    val conditionBean = new DataCenterConditionBean()
    conditionBean.init(map)
    conditionBean
  }
}


class Entry {
  var dataCenter : String = _
  var flowName : String = _
  var appId : String = _

  def init(map : Map[String, String]): Unit ={
    this.dataCenter = MapUtil.get(map,"dataCenter").asInstanceOf[String]
    this.flowName = MapUtil.get(map,"flowName").asInstanceOf[String]
    this.appId = ""
  }
}

object Entry{
  def apply(map : Map[String, String]): Entry = {
    val entry = new Entry()
    entry.init(map)
    entry
  }
}
