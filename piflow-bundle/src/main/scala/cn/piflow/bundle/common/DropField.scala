package cn.piflow.bundle.common

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}


class DropField extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Delete fields in schema"
  val inportList: List[String] = List(Port.DefaultPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)

  var fields:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    var df = in.read()

    val field = fields.split(",")
    for( x <- 0 until field.size){
      df = df.drop(field(x))
    }

    out.write(df)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    fields = MapUtil.get(map,"fields").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val inports = new PropertyDescriptor().name("fields").displayName("Fields")
      .description("Delete fields in schema,multiple are separated by commas")
      .defaultValue("")
      .required(true)
      .example("id")
    descriptor = inports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/DropField.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }

}



