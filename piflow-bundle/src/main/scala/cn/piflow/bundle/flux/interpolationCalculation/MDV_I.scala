package cn.piflow.bundle.flux.interpolationCalculation

import cn.piflow.bundle.flux.util.FluxInterpolationUtil_4
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class MDV_I extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Interpolation algorithm: MDV-I: fixed window;Schema must contain hour, day_id fields (id incremented by date)"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var fields: String = _
  var mdv_num: String = _
  var qualityControlMarkerValue: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val flux = new FluxInterpolationUtil_4
    val df = flux.MDVFixed(spark, in.read(),fields,mdv_num.toInt,qualityControlMarkerValue.toInt)

    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    fields = MapUtil.get(map,"fields").asInstanceOf[String]
    mdv_num = MapUtil.get(map,"mdv_num").asInstanceOf[String]
    qualityControlMarkerValue = MapUtil.get(map,"qualityControlMarkerValue").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val fields = new PropertyDescriptor()
      .name("fields")
      .displayName("fields")
      .description("Fields that need to be interpolated, separated by commas")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = fields :: descriptor

    val mdv_num = new PropertyDescriptor()
      .name("mdv_num")
      .displayName("mdv_num")
      .description("Window time")
      .defaultValue("7")
      .required(true)
      .example("7")
    descriptor = mdv_num :: descriptor

    val qualityControlMarkerValue = new PropertyDescriptor()
      .name("qualityControlMarkerValue")
      .displayName("qualityControlMarkerValue")
      .description("质量控制标记值:Quality control marker value")
      .defaultValue("-9999")
      .required(true)
      .example("-9999")
    descriptor = qualityControlMarkerValue :: descriptor


    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("png/Flux/flux.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List("Flux_interpolationCalculation")
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
