package cn.piflow.bundle.common

import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

class Fork extends ConfigurableStop{

  var outports : List[String] = _

  override def setProperties(map: Map[String, Any]): Unit = {
    outports = MapUtil.get(map,"outports").asInstanceOf[List[String]]
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    outports.foreach(out.write(_, in.read()));
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = ???
}
