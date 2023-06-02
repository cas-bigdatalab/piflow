package cn.piflow.bundle.flux.pretreatment

import cn.piflow.bundle.flux.util.FluxUtil_1
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class SingleFieldThresholdClean extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Threshold cleaning of the fields,Include upper and lower limits"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var fields: String = _
  var maxValue: String = _
  var minValue: String = _
  var flagValue: String = _
  var additionalCondition: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val flux = new FluxUtil_1
    val df = flux.singleFieldThresholdCleaning(spark, in.read(),fields, maxValue, minValue,flagValue,additionalCondition)

    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    fields = MapUtil.get(map,"fields").asInstanceOf[String]
    maxValue = MapUtil.get(map,"maxValue").asInstanceOf[String]
    minValue = MapUtil.get(map,"minValue").asInstanceOf[String]
    flagValue = MapUtil.get(map,"flagValue").asInstanceOf[String]
    additionalCondition = MapUtil.get(map,"additionalCondition").asInstanceOf[String]

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

    val maxValue = new PropertyDescriptor()
      .name("maxValue")
      .displayName("maxValue")
      .description("Upper threshold")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = maxValue :: descriptor

    val minValue = new PropertyDescriptor()
      .name("minValue")
      .displayName("minValue")
      .description("Lower threshold")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = minValue :: descriptor

    val flagValue = new PropertyDescriptor()
      .name("flagValue")
      .displayName("flagValue")
      .description("Identification value")
      .defaultValue("-9999")
      .required(true)
      .example("")
    descriptor = flagValue :: descriptor

    val additionalCondition = new PropertyDescriptor()
      .name("additionalCondition")
      .displayName("additionalCondition")
      .description("Additional condition")
      .defaultValue("1=1")
      .required(true)
      .example("")
    descriptor = additionalCondition :: descriptor


    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("png/Flux/flux.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CleanGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
