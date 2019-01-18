package cn.piflow.bundle.common

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}


class ConvertSchema extends ConfigurableStop {

  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "Transform field name"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var schema:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    var df = in.read()

    val field = schema.split(",")

    field.foreach(f => {
      val old_new: Array[String] = f.split("->")
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
    val inports = new PropertyDescriptor().name("schema").displayName("schema").description("To change the field name of the name and the name you want, " +
      "you can write oldField1 - > newField1, if there are more than one, you can use, partition, such as oldField1->newField1, oldField2->newField2").defaultValue("").required(true)
    descriptor = inports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("common/convert.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }

}



