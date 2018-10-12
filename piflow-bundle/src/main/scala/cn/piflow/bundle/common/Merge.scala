package cn.piflow.bundle.common

import cn.piflow.conf.{CommonGroup, ConfigurableStop, StopGroup, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

import scala.beans.BeanProperty

class Merge extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val inportCount: Int = -1
  val outportCount: Int = 1

  var inports : List[String] = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    out.write(in.ports().map(in.read(_)).reduce((x, y) => x.union(y)));
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val inports = new PropertyDescriptor().name("inports").displayName("inports").description("inports list").defaultValue("").required(true)
    descriptor = inports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/selectHiveQL.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.CommonGroup.toString)
  }

}
