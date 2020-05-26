package cn.piflow.bundle.common

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

class Merge extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Merge data into one stop"
  val inportList: List[String] = List(Port.AnyPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var inports : List[String] = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    out.write(in.ports().map(in.read(_)).reduce((x, y) => x.union(y)));
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    val inportStr = MapUtil.get(map,"inports").asInstanceOf[String]
    inports = inportStr.split(",").map(x => x.trim).toList
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val inports = new PropertyDescriptor()
      .name("inports")
      .displayName("Inports")
      .description("Inports string are separated by commas")
      .defaultValue("")
      .required(true)
    descriptor = inports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/Merge.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }

}
