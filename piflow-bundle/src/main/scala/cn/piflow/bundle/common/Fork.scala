package cn.piflow.bundle.common

import cn.piflow.conf.{CommonGroup, ConfigurableStop, StopGroup, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

import scala.beans.BeanProperty

class Fork extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val inportCount: Int = 1
  val outportCount: Int = -1

  var outports : List[String] = _

  override def setProperties(map: Map[String, Any]): Unit = {
    outports = MapUtil.get(map,"outports").asInstanceOf[List[String]]
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    outports.foreach(out.write(_, in.read()));
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val outports = new PropertyDescriptor().name("outports").displayName("outports").description("outports list").defaultValue("").required(true)
    descriptor = outports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/selectHiveQL.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.CommonGroup.toString)
  }

}
