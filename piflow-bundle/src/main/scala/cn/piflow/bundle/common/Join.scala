package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{Column, DataFrame}

class Join extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Table connection, including full connection, left connection, right connection and inner connection"
  override val inportList: List[String] =List(Port.LeftPort.toString,Port.RightPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)

  var joinMode:String=_
  var correlationField:String=_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val leftDF =  in.read(Port.LeftPort)
    val rightDF = in.read(Port.RightPort)

    var seq: Seq[String]= Seq()
    correlationField.split(",").foreach(x=>{
      seq = seq .++(Seq(x.toString))
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
    correlationField = MapUtil.get(map,"correlationField").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val joinMode = new PropertyDescriptor().name("joinMode")
      .displayName("joinMode")
      .description("For table association, you can choose INNER, LEFT, RIGHT, FULL")
      .allowableValues(Set("inner","left","right","full_outer"))
      .defaultValue("inner")
      .required(true)
    descriptor = joinMode :: descriptor

    val correlationField = new PropertyDescriptor()
      .name("correlationField")
      .displayName("correlationField")
      .description("Fields associated with tables,If there are more than one, please use , separate")
      .defaultValue("")
      .required(true)
    descriptor = correlationField :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/Join.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
