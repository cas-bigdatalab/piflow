package cn.piflow.bundle.flux.dataCheck

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class ConsistencyCheck extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Quality control of grassland aboveground biomass data,Consistency check"
  override val inportList: List[String] =List(Port.LeftPort,Port.RightPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var flagField:String=_
  var correlationColumn:String=_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    in.read(Port.LeftPort).createOrReplaceTempView("leftTable")
    in.read(Port.RightPort).createOrReplaceTempView("rightTable")

    val strings = correlationColumn.split(",")
    val stringBuilder = new StringBuilder
    strings.foreach(x=>{
      stringBuilder.append(" a."+x + "=b."+x)
      stringBuilder.append(" and")
    })

    val outdf = spark.sql(
      s"""
         |select if(b.${strings(0)} is null ,1,0) as  ${flagField} ,a.*    from leftTable a
         | left join rightTable b on ${stringBuilder.toString().stripSuffix("and")}
         |""".stripMargin)

    out.write(outdf)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    flagField = MapUtil.get(map,"flagField").asInstanceOf[String]
    correlationColumn = MapUtil.get(map,"correlationColumn").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val joinMode = new PropertyDescriptor()
      .name("flagField")
      .displayName("flagField")
      .description("Consistency check and set the flag field to 0 consistently and 1 otherwise")
      .defaultValue("flag")
      .required(true)
      .example("flag")
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
    ImageUtil.getImage("png/common/Join.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ExcelGroup)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
