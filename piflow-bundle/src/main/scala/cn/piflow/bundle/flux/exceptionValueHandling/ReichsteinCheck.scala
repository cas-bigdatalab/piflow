package cn.piflow.bundle.flux.exceptionValueHandling

import cn.piflow.bundle.flux.util.Reichstein
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

/**
 * @Author renhao
 * @Description:
 * @Data 2023/3/2 18:13
 * @Modified By:
 */
class ReichsteinCheck extends ConfigurableStop{
  override val authorEmail: String = "rh@cnic.cn"
  override val description: String = "Handling of outliers by Reichstein"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var soilTemperatureField: String = _
  var frictionWindSpeedField: String = _
  var FC: String = _
  var flagValue: Integer = _
  var percentFlux: Double = _

//  val metroJoinFlux = metroCBS.join(fluxCBS, Seq("year", "month", "day", "hour"), "left")
  //    //5cm土壤温度m5
  //    val soilTemperatureField = "Ts_107_1_AVG"
  //    //摩擦风速字段，即U*
  //    val FrictionWindSpeedField = "p5"
  //    //FC值 CO2通量 NEE
  //    val FC = "p1"
  //    val flagValue = -99999
  //    //设置通量百分比
  //    val percentFlux = 0.99

  override def setProperties(map: Map[String, Any]): Unit = {
    soilTemperatureField = MapUtil.get(map, "soilTemperatureField").asInstanceOf[String]
    frictionWindSpeedField = MapUtil.get(map, "frictionWindSpeedField").asInstanceOf[String]
    FC = MapUtil.get(map, "FC").asInstanceOf[String]
    flagValue = MapUtil.get(map, "flagValue").asInstanceOf[Integer]
    percentFlux = MapUtil.get(map, "percentFlux").asInstanceOf[Double]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()

    val soilTemperatureField = new PropertyDescriptor()
      .name("soilTemperatureField")
      .displayName("soilTemperatureField")
      .description("5cm soil temperature field name")
      .defaultValue("")
      .required(true)
      .example("Ts_107_1_AVG")
    descriptor = soilTemperatureField :: descriptor

    val frictionWindSpeedField = new PropertyDescriptor()
      .name("frictionWindSpeedField")
      .displayName("frictionWindSpeedField")
      .description("Friction wind speed field name")
      .defaultValue("")
      .required(true)
      .example("p5")
    descriptor = frictionWindSpeedField :: descriptor

    val FC = new PropertyDescriptor()
      .name("FC")
      .displayName("FC")
      .description("FC flux field name")
      .defaultValue("")
      .required(true)
      .example("p2")
    descriptor = FC :: descriptor

    val flagValue = new PropertyDescriptor()
      .name("flagValue")
      .displayName("flagValue")
      .description("invalid value")
      .defaultValue("-99999")
      .required(true)
      .example("-99999")
    descriptor = flagValue :: descriptor

    val percentFlux = new PropertyDescriptor()
      .name("percentFlux")
      .displayName("percentFlux")
      .description("Percent flux")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = percentFlux :: descriptor

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

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val reichstein = new Reichstein
    val df = reichstein.reichsteinCorrectU(spark,in.read(),soilTemperatureField,frictionWindSpeedField,FC,flagValue,percentFlux)
    out.write(df)
  }
}
