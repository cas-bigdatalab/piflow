package cn.piflow.bundle.common

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.lib._
import cn.piflow.util.ScriptEngine


class DoFlatMapStop extends ConfigurableStop{


  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "DoFlatMap Stop."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var  SCRIPT: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    in.read().show()

    val doMap = new  DoFlatMap(ScriptEngine.logic(SCRIPT))
    doMap.perform(in,out,pec)

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    SCRIPT = MapUtil.get(map,"SCRIPT_2").asInstanceOf[String]

  }
  override def initialize(ctx: ProcessContext): Unit = {

  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val SCRIPT = new PropertyDescriptor().name("SCRIPT").displayName("SCRIPT").description("").defaultValue("").required(true)
    descriptor = SCRIPT :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/DoFlatMap.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }



}



