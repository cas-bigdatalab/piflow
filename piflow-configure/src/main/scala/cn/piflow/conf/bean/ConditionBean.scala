package cn.piflow.conf.bean

import cn.piflow.conf.util.MapUtil

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */
class ConditionBean {

  var entry : String = _
  var after : List[String] = _

  def init(entry:String, after: String)= {
    this.entry = entry
    this.after = after.split(",").toList
  }
  def init(map:Map[String,Any])= {
    this.entry = MapUtil.get(map,"entry").asInstanceOf[String]
    this.after = MapUtil.get(map,"after").asInstanceOf[String].split(",").toList
  }

}
object ConditionBean{

  def apply(map : Map[String, Any]): ConditionBean = {
    val conditionBean = new ConditionBean()
    conditionBean.init(map)
    conditionBean
  }
}
