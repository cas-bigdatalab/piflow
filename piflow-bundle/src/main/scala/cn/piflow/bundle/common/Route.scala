package cn.piflow.bundle.common

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

class Route extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Route data by custom properties,key is port,value is filter"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.RoutePort)

  override val isCustomized: Boolean = true

  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read().cache()

    if(this.customizedProperties != null || this.customizedProperties.size != 0){
      val it = this.customizedProperties.keySet.iterator
      while (it.hasNext){
        val port = it.next()
        val filterCondition = MapUtil.get(this.customizedProperties,port).asInstanceOf[String]
        val filterDf = df.filter(filterCondition)
        out.write(port,filterDf)
      }
    }
    out.write(df);
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/Fork.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }
}
