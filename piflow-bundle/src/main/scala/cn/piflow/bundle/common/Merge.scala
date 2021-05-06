package cn.piflow.bundle.common

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}

class Merge extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Merge multi source."
  override val inportList: List[String] = List(Port.AnyPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var inports : List[String] = _

  override def setProperties(map: Map[String, Any]): Unit = {
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

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    out.write(in.ports().map(in.read(_)).reduce((x, y) => x.union(y)));
  }
}
