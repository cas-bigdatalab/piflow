package cn.piflow.bundle.common

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}


class ConvertSchema extends ConfigurableStop {

  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "Change field name"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var schema:String = _
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    var df = in.read()

    val field = schema.split(",").map(x => x.trim)

    field.foreach(f => {
      val old_new: Array[String] = f.split("->").map(x => x.trim)
      df = df.withColumnRenamed(old_new(0),old_new(1))
    })

    out.write(df)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val inports = new PropertyDescriptor().name("schema")
      .displayName("Schema")
      .description("Change column names,multiple column names are separated by commas")
      .defaultValue("")
      .required(true)
      .example("id->uuid")
    descriptor = inports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/ConvertSchema.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }

}



