package cn.piflow

import cn.piflow.util.MapUtil

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */
class DataCenterConditionBean {

  var entry : Entry = _
  var after : List[Entry] = _

  def init(map:Map[String,Any])= {
    val afterMap = MapUtil.get(map,"after").asInstanceOf[Map[String, String]]
    this.after = Entry(afterMap) +: this.after

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
  var outport : String = _
  var appId : String = _

  def init(map : Map[String, String]): Unit ={
    this.dataCenter = MapUtil.get(map,"dataCenter").asInstanceOf[String]
    this.flowName = MapUtil.get(map,"flowName").asInstanceOf[String]
    this.outport = MapUtil.get(map,"outport").asInstanceOf[String]
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
