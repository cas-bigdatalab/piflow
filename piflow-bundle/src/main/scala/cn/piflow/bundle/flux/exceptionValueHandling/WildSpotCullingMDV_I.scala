package cn.piflow.bundle.flux.exceptionValueHandling

import cn.piflow.bundle.flux.util.FluxOutlierHandlingUtil_3
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class WildSpotCullingMDV_I extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Using a fixed window, the standard deviation or variance is calculated " +
    " within a specified size window. * for data exceeding x times " +
    " variance or standard deviation, the quality control is marked as Ao and eliminated."
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var fields: String = _
  var mdv_num: String = _
  var multiple: String = _
  var statisticalType: String = _
  var flagValue: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val fluxCBS = in.read()

    val flux = new FluxOutlierHandlingUtil_3
    val df = flux.FluxOutfieldEMDVFixed(spark,fluxCBS,fields,mdv_num.toInt,multiple.toDouble,statisticalType,flagValue)

    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    fields = MapUtil.get(map,"fields").asInstanceOf[String]
    mdv_num = MapUtil.get(map,"mdv_num").asInstanceOf[String]
    multiple = MapUtil.get(map,"multiple").asInstanceOf[String]
    statisticalType = MapUtil.get(map,"statisticalType").asInstanceOf[String]
    flagValue = MapUtil.get(map,"flagValue").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val fields = new PropertyDescriptor()
      .name("fields")
      .displayName("fields")
      .description("Threshold processing fields, multiple separated by commas")
      .defaultValue("")
      .required(true)
      .example("a,b")
    descriptor = fields :: descriptor

    val mdv_num = new PropertyDescriptor()
      .name("mdv_num")
      .displayName("mdv_num")
      .description("Window time")
      .defaultValue("7")
      .required(true)
      .example("")
    descriptor = mdv_num :: descriptor

    val multiple = new PropertyDescriptor()
      .name("multiple")
      .displayName("multiple")
      .description("Multiple of statistical type")
      .defaultValue("1")
      .required(true)
      .example("")
    descriptor = multiple :: descriptor

    val statisticalType = new PropertyDescriptor()
      .name("statisticalType")
      .displayName("statisticalType")
      .description("Calculation type,Variance or standard deviation (stddev,variance)")
      .defaultValue("stddev")
      .required(true)
      .example("")
    descriptor = statisticalType :: descriptor


    val flagValue = new PropertyDescriptor()
      .name("flagValue")
      .displayName("flagValue")
      .description("Identification value")
      .defaultValue("")
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
