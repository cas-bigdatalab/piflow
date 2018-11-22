package cn.piflow.bundle.common

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}


class ConvertSchema extends ConfigurableStop {

  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "convert data field."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var schema:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()

    //oldField1->newField1, oldField2->newField2
    val field = schema.split(",")

    field.foreach(f => {
      val old_new: Array[String] = f.split("->")
      df.withColumnRenamed(old_new(0),old_new(1))
    })

    println("###########################")
    df.show(20)
    println("###########################")

    out.write(df)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val inports = new PropertyDescriptor().name("schema").displayName("schema").description("The Schema you want to convert,You can write like this: oldField1->newField1, oldField2->newField2").defaultValue("").required(true)
    descriptor = inports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("convert.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.CommonGroup.toString)
  }

}



