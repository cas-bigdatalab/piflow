package cn.piflow.schedule

/**
  * Created by xjzhu@cnic.cn on 4/25/19
  */

trait Execution {

  def isEntryCompleted(name : String) : Boolean

}
