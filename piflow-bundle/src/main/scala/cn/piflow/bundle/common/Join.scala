package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{Column, DataFrame}

class Join extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Table join"
  override val inportList: List[String] =List(PortEnum.AnyPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var joinMode:String=_
  var correlationField:String=_



  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val dfs: Seq[DataFrame] = in.ports().map(in.read(_))
    var df1: DataFrame = dfs(0)
    var df2: DataFrame = dfs(1)
    var column: Column = null

    val correlationFieldArr: Array[String] = correlationField.split(",")
    df1 = df1.withColumnRenamed(correlationFieldArr(0),correlationFieldArr(0)+"_1")
    df2 = df2.withColumnRenamed(correlationFieldArr(0),correlationFieldArr(0)+"_2")
    column = df1(correlationFieldArr(0)+"_1")===df2(correlationFieldArr(0)+"_2")
    if(correlationFieldArr.size > 1){
      for(x <- (1 until correlationFieldArr.size)){
        var newColumn: Column =null
          df1 = df1.withColumnRenamed(correlationFieldArr(x),correlationFieldArr(x)+"_1")
          df2 = df2.withColumnRenamed(correlationFieldArr(x),correlationFieldArr(x)+"_2")
          newColumn = df1(correlationFieldArr(x)+"_1")===df2(correlationFieldArr(x)+"_2")
          column = column and newColumn
      }
    }

    var df: DataFrame = null
    joinMode match {
      case "INNER" =>df = df1.join(df2, column)
      case "LEFT" => df = df1.join(df2,column,"left_outer")
      case "RIGHT" => df = df1.join(df2,column,"right_outer")
      case "FULL" => df = df1.join(df2,column,"outer")
    }
    println("######################################")
    df.show(20)
    out.write(df)

  }



  override def setProperties(map: Map[String, Any]): Unit = {
    joinMode = MapUtil.get(map,"joinMode").asInstanceOf[String]
    correlationField = MapUtil.get(map,"correlationField").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val joinMode = new PropertyDescriptor().name("joinMode").displayName("joinMode").description("For table association, you can choose INNER, LEFT, RIGHT, FULL").defaultValue("").required(true)
    val correlationField = new PropertyDescriptor().name("correlationField").displayName("correlationField").description("Fields associated with tables,If there are more than one, please use, separate").defaultValue("").required(true)
    descriptor = correlationField :: descriptor
    descriptor = joinMode :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("/common/join.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
