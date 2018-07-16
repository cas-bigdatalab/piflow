package cn.piflow.bundle.common

import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

class Merge extends ConfigurableStop{

  var inports : List[String] = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    out.write(in.ports().map(in.read(_)).reduce((x, y) => x.union(y)));
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = ???
}
