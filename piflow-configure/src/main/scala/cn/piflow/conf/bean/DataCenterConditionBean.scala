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

  def init(after:List[Entry], outport:String, inport:String, entry:Entry) = {
    this.after = after
    this.outport = outport
    this.inport = inport
    this.entry = entry
  }

  def copy() : DataCenterConditionBean = {
    val conditionBean = new DataCenterConditionBean()
    var afterCopy = List[Entry]()
    after.foreach( a => {
      val entry = Entry(a.dataCenter, a.flowName, a.appId)
      afterCopy = entry +: afterCopy
    })
    val entryCopy = Entry(entry.dataCenter, entry.flowName, entry.appId)
    conditionBean.init(afterCopy, outport, inport, entryCopy)
    conditionBean
  }
}

object DataCenterConditionBean{

  def apply(map : Map[String, Any]): DataCenterConditionBean = {
    val conditionBean = new DataCenterConditionBean()
    conditionBean.init(map)
    conditionBean
  }

  def apply(after:List[Entry], outport:String, inport:String, entry:Entry): DataCenterConditionBean = {
    val conditionBean = new DataCenterConditionBean()
    conditionBean.init(after, outport, inport, entry)
    conditionBean
  }
}


class Entry {
  var dataCenter : String = _
  var flowName : String = _
  var appId : String = _

  def init(map : Map[String, String]): Unit ={
    this.dataCenter = map.getOrElse("dataCenter","")
    this.flowName = map.getOrElse("flowName","")
    this.appId = ""
  }

  def init(dataCenter:String, flowName:String, appId:String): Unit ={
    this.dataCenter = dataCenter
    this.flowName = flowName
    this.appId = appId
  }
}

object Entry{
  def apply(map : Map[String, String]): Entry = {
    val entry = new Entry()
    entry.init(map)
    entry
  }

  def apply(dataCenter:String, flowName:String, appId:String): Entry = {
    val entry = new Entry()
    entry.init(dataCenter, flowName, appId)
    entry
  }
}
