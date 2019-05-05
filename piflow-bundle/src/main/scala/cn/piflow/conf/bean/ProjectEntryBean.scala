package cn.piflow.conf.bean

import cn.piflow.conf.util.MapUtil
import cn.piflow.{Condition, FlowGroupImpl, ProjectEntry}

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */
trait ProjectEntryBean {

  var uuid : String
  var name : String


  def init(map : Map[String, Any])

}


