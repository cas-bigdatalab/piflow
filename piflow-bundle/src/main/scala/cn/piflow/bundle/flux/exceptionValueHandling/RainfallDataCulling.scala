package cn.piflow.bundle.flux.exceptionValueHandling

import cn.piflow.bundle.flux.util.FluxOutlierHandlingUtil_3
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class RainfallDataCulling extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Elimination of rainfall data in the same period(The occurrence of precipitation disturbs " +
    "the normal atmospheric flow in the ecosystem and leads to instrument failure, " +
    "so it is necessary to eliminate the precipitation observation data at the same time to ensure the data quality.)"
  val inportList: List[String] = List("fluxCbsPort","metroCbsPort")
  val outportList: List[String] = List(Port.DefaultPort)

  var fields: String = _
  var rainFallField: String = _
  var flagValue: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val metroCBS = in.read("metroCbsPort")
    val fluxCBS = in.read("fluxCbsPort")

    val flux = new FluxOutlierHandlingUtil_3
    val df = flux.RainfallDataCulling(spark,metroCBS,fluxCBS,fields,rainFallField,flagValue.toInt)
    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    fields = MapUtil.get(map,"fields").asInstanceOf[String]
    rainFallField = MapUtil.get(map,"rainFallField").asInstanceOf[String]
    flagValue = MapUtil.get(map,"flagValue").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val fields = new PropertyDescriptor()
      .name("fields")
      .displayName("fields")
      .description("Threshold processing fields, multiple separated by commas")
      .defaultValue("Fc,LE,Hs")
      .required(true)
      .example("a,b")
    descriptor = fields :: descriptor

    val rainFallField = new PropertyDescriptor()
      .name("rainFallField")
      .displayName("rainFallField")
      .description("Meteorological data rainfall")
      .defaultValue("Rain_0_TOT")
      .required(true)
      .example("")
    descriptor = rainFallField :: descriptor


    val flagValue = new PropertyDescriptor()
      .name("flagValue")
      .displayName("flagValue")
      .description("Identification value")
      .defaultValue("-9999")
      .required(true)
      .example("")
    descriptor = flagValue :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("png/Flux/flux.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List("Flux_exceptionValueHandling")
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
