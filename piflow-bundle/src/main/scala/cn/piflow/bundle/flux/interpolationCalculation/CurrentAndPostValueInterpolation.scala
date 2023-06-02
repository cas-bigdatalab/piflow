package cn.piflow.bundle.flux.interpolationCalculation

import cn.piflow.bundle.flux.util.FluxInterpolationUtil_4
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class CurrentAndPostValueInterpolation extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "TThe current value is invalid M(k), M (k+1) is invalid, M (k-1) is valid, and M (k+2) is valid.;Schema must contain hour, day_id fields (id incremented by date)"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var fields: String = _
  var qualityControlMarkerValue: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val metroCBS = in.read()

    val fluxInterpolation = new FluxInterpolationUtil_4

    val interpolationResultDF = fluxInterpolation.CurrentAndPostValueInterpolation(spark,metroCBS,fields,-9999)


    out.write(interpolationResultDF)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    fields = MapUtil.get(map,"fields").asInstanceOf[String]
    qualityControlMarkerValue = MapUtil.get(map,"qualityControlMarkerValue").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val fields = new PropertyDescriptor()
      .name("fields")
      .displayName("fields")
      .description("Fields that need to be interpolated, separated by commas")
      .defaultValue("Ta_1_AVG,Pvapor_1_AVG,DR_5_CM11_AVG,PAR_7_AVG,Ts_107_1_AVG,Smoist_20cm_AVG,Ta_2_AVG,Ta_3_AVG,Pvapor_2_AVG,Pvapor_3_AVG,Ta_4_AVG,Ta_5_AVG,Pvapor_4_AVG,Pvapor_5_AVG,Ta_6_AVG,Ta_7_AVG,Pvapor_6_AVG,Pvapor_7_AVG")
      .required(true)
      .example("")
    descriptor = fields :: descriptor

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
