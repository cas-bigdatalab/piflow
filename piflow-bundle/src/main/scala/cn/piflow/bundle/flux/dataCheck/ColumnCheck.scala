package cn.piflow.bundle.flux.dataCheck

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

class ColumnCheck extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Quality control of grassland aboveground biomass data,Consistency check"
  override val inportList: List[String] =List(Port.LeftPort,Port.RightPort)
  override val outportList: List[String] = List(Port.DefaultPort)

//  var flagField:String=_
//  var correlationColumn:String=_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val leftDf  = in.read(Port.LeftPort)
    val rightDF =in.read(Port.RightPort)

    val leftNmes: Array[String] = leftDf.schema.fieldNames
    val rightNmes: Array[String] = rightDF.schema.fieldNames

    for (i<- 0 until leftNmes.size){
      if(leftNmes(i) != rightNmes(i)) throw new Exception("warn!!! 表头名称及量纲与标准表格的一致性检查 不一致 ")
    }
    out.write(leftDf)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
//    flagField = MapUtil.get(map,"flagField").asInstanceOf[String]
//    correlationColumn = MapUtil.get(map,"correlationColumn").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

//    val joinMode = new PropertyDescriptor()
//      .name("flagField")
//      .displayName("flagField")
//      .description("Consistency check and set the flag field to 0 consistently and 1 otherwise")
//      .defaultValue("flag")
//      .required(true)
//      .example("flag")
//    descriptor = joinMode :: descriptor
//
//    val correlationColumn = new PropertyDescriptor()
//      .name("correlationColumn")
//      .displayName("CorrelationColumn")
//      .description("Columns associated with tables,if multiple are separated by commas")
//      .defaultValue("")
//      .required(true)
//      .example("id,name")
//    descriptor = correlationColumn :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("png/common/Join.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ExcelGroup)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
