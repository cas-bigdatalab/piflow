package cn.piflow.conf

import cn.piflow.util.{HdfsUtil, PropertyUtil}
import cn.piflow.{IncrementalStop, JobContext}

/**
  * Created by xjzhu@cnic.cn on 7/15/19
  */
abstract class ConfigurableIncrementalStop extends ConfigurableStop with IncrementalStop {


  override var incrementalPath: String = _

  override def init(flowName : String, stopName : String): Unit = {
    incrementalPath = PropertyUtil.getPropertyValue("increment.path").stripSuffix("/") + "/" + flowName + "/" + stopName

  }

  override def readIncrementalStart(): String = {
    if( HdfsUtil.exists(incrementalPath) == false)
      HdfsUtil.createFile(incrementalPath)
    var value:String = HdfsUtil.getLine(incrementalPath)
    value
  }

  override def saveIncrementalStart(value: String): Unit = {
    HdfsUtil.saveLine(incrementalPath, value)
  }

}
