package cn.piflow.conf.bean

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */
trait GroupEntryBean {

  var uuid : String
  var name : String


  def init(map : Map[String, Any])

}


