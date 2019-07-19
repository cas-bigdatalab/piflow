package cn.piflow.conf

import cn.piflow.util.{HdfsUtil, PropertyUtil}
import cn.piflow.{IncrementalStop, JobContext}

/**
  * Created by xjzhu@cnic.cn on 7/15/19
  */
abstract class ConfigurableIncrementalStop extends ConfigurableStop with IncrementalStop {


  override var incrementalValue: String = _
  override var incrementalPath: String = _

  override def init(flowName : String, stopName : String): Unit = {
    incrementalPath = PropertyUtil.getPropertyValue("increment.path") + "/" + flowName + "/" + stopName
    incrementalValue = readIncrementalValue()

  }

  override def readIncrementalValue(): String = {
    var value:String = HdfsUtil.getLine(incrementalPath)
    if(value == null || value == "")
      value = "0"
    value
  }

  override def saveIncrementalValue(value: String): Unit = {
    HdfsUtil.saveLine(incrementalPath, value)
    incrementalValue = value
  }

}
