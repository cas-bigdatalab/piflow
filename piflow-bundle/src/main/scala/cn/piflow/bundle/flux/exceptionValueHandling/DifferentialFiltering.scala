package cn.piflow.bundle.flux.exceptionValueHandling

import cn.piflow.bundle.flux.util.FluxOutlierHandlingUtil_3
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class DifferentialFiltering extends ConfigurableStop {
  val authorEmail: String = "wkn@cnic.cn"
  val description: String = "Difference algorithm: di is defined as the difference between twice the current flux value and the sum of the former and the latter. The flux is normal when di is within a certain range, otherwise, it`s abnormal"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var fields: String = _
  var para_Z: String = _
  var qualityControlMarkerValue: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val flux = new FluxOutlierHandlingUtil_3
    var originDF = in.read()

    fields.split(",").foreach(x => {
      originDF = flux.FluxDifference(spark, originDF, x, para_Z.toDouble, qualityControlMarkerValue)
    })

    out.write(originDF)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    fields = MapUtil.get(map, "fields").asInstanceOf[String]
    para_Z = MapUtil.get(map, "para_Z").asInstanceOf[String]
    qualityControlMarkerValue = MapUtil.get(map, "qualityControlMarkerValue").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()

    val fields = new PropertyDescriptor()
      .name("fields")
      .displayName("fields")
      .description("Fields that need to be interpolated, separated by commas")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = fields :: descriptor

    val para_Z = new PropertyDescriptor()
      .name("para_Z")
      .displayName("para_Z")
      .description("Sensitivity, usually is 4, 5.5, 7.")
      .defaultValue("4")
      .required(true)
      .example("4")
    descriptor = para_Z :: descriptor

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
    List("Flux_exceptionValueHandling")
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
