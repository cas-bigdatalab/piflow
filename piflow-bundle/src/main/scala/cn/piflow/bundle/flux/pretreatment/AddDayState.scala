package cn.piflow.bundle.flux.pretreatment

import cn.piflow.bundle.flux.util.FluxUtil_1
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class AddDayState extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Add the state of the current time based on the id of the day, month, day, hour and day (day or night (defined by sunrise and sunset))"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var longitude: String = _
  var latitude: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val flux = new FluxUtil_1
    val df = flux.AddDayStateWithDayHour(spark, in.read(),longitude.toDouble, latitude.toDouble)

    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    longitude = MapUtil.get(map,"longitude").asInstanceOf[String]
    latitude = MapUtil.get(map,"latitude").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val longitude = new PropertyDescriptor()
      .name("longitude")
      .displayName("longitude")
      .description("longitude")
      .defaultValue("128.1")
      .required(true)
      .example("128.1")
    descriptor = longitude :: descriptor

    val latitude = new PropertyDescriptor()
      .name("latitude")
      .displayName("latitude")
      .description("latitude")
      .defaultValue("42.4")
      .required(true)
      .example("42.4")
    descriptor = latitude :: descriptor


    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("png/Flux/flux.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List("Flux_pretreatment")
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
