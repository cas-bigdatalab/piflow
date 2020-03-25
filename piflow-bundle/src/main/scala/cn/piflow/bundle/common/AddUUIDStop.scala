package cn.piflow.bundle.common

import java.util.UUID

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, SparkSession}

class AddUUIDStop extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"



  override val description: String = "Add  UUID column"
  override val inportList: List[String] =List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)


  var column:String=_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark =  pec.get[SparkSession]()
    var df = in.read()


    spark.udf.register("generaterUUID",()=>UUID.randomUUID().toString.replace("-",""))

    df.createOrReplaceTempView("temp")
    df = spark.sql(s"select generaterUUID() as ${column},* from temp")

    out.write(df)

  }



  override def setProperties(map: Map[String, Any]): Unit = {
    column = MapUtil.get(map,"column").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()


    val column = new PropertyDescriptor().name("column")
      .displayName("Column")
      .description("The column is you want to add uuid column's name,")
      .defaultValue("uuid")
      .required(true)
      .example("uuid")
    descriptor = column :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/addUUID.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
