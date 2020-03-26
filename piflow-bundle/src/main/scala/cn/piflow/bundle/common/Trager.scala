package cn.piflow.bundle.common

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

class Trager extends ConfigurableStop{

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Upstream and downstream middleware"
  val inportList: List[String] = List(Port.AnyPort)
  val outportList: List[String] = List(Port.AnyPort)


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/trager.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }

}
