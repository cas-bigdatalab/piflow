package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{Column, DataFrame}

class Join extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Table joins include full join, left join, right join and inner join"
  override val inportList: List[String] =List(Port.LeftPort,Port.RightPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var joinMode:String=_
  var correlationColumn:String=_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val leftDF =  in.read(Port.LeftPort)
    val rightDF = in.read(Port.RightPort)

    var seq: Seq[String]= Seq()
    correlationColumn.split(",").foreach(x=>{
      seq = seq .++(Seq(x.trim.toString))
    })

    var df: DataFrame = null
    joinMode match {
      case "inner" =>df = leftDF.join(rightDF, seq)
      case "left" => df = leftDF.join(rightDF,seq,"left_outer")
      case "right" => df = leftDF.join(rightDF,seq,"right_outer")
      case "full_outer" => df = leftDF.join(rightDF,seq,"outer")
    }
    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    joinMode = MapUtil.get(map,"joinMode").asInstanceOf[String]
    correlationColumn = MapUtil.get(map,"correlationColumn").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val joinMode = new PropertyDescriptor()
      .name("joinMode")
      .displayName("JoinMode")
      .description("For table associations, you can choose inner,left,right,full")
      .allowableValues(Set("inner","left","right","full_outer"))
      .defaultValue("inner")
      .required(true)
      .example("left")
    descriptor = joinMode :: descriptor

    val correlationColumn = new PropertyDescriptor()
      .name("correlationColumn")
      .displayName("CorrelationColumn")
      .description("Columns associated with tables,if multiple are separated by commas")
      .defaultValue("")
      .required(true)
      .example("id,name")
    descriptor = correlationColumn :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/Join.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
