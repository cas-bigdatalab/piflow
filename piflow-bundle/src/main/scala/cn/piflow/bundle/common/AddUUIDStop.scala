package cn.piflow.bundle.common

import java.util.UUID

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, SparkSession}

class AddUUIDStop extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Increase the column with uuid"
  override val inportList: List[String] =List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)


  var column:String=_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark =  pec.get[SparkSession]()
    var df = in.read()


    val sqlContext = spark.sqlContext
    val name  = df.schema(0).name
    sqlContext.udf.register("code",(str:String)=>UUID.randomUUID().toString.replace("-",""))

    val columns = column.split(",")
    columns.foreach(t=>{
      df.createOrReplaceTempView("temp")
      df = sqlContext.sql("select code("+name+") as "+t +",* from temp")
    })
    out.write(df)

  }



  override def setProperties(map: Map[String, Any]): Unit = {
    column = MapUtil.get(map,"column").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val inports = new PropertyDescriptor().name("column").displayName("column")
      .description("The column is you want to add uuid column's name,Multiple are separated by commas").defaultValue("uuid").required(true)
    descriptor = inports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/addUUID.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
