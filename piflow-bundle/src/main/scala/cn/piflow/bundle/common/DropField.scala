package cn.piflow.bundle.common

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}


class DropField extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Delete one or more columns"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var columnNames:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    var df = in.read()

    val field = columnNames.split(",").map(x => x.trim)
    for( x <- 0 until field.size){
      df = df.drop(field(x))
    }

    out.write(df)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    columnNames = MapUtil.get(map,"columnNames").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val inports = new PropertyDescriptor()
      .name("columnNames")
      .displayName("ColumnNames")
      .description("Fill in the columns you want to delete,multiple columns names separated by commas")
      .defaultValue("")
      .required(true)
      .example("id")
    descriptor = inports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/DropColumnNames.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }

}



