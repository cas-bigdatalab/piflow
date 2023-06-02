package cn.piflow.bundle.flux.dataCorrection

import cn.piflow.bundle.flux.util.FluxDataCorrectionUtil_2
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class DRCoordinateRotation extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Quadratic coordinate rotation(DR)"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var Fc: String = _
  var Le: String = _
  var Hs: String = _

  var u_star: String = _
  var cov_Uz_Uz	:String = _
  var cov_Uz_Ux	:String = _
  var cov_Uz_Uy	:String = _
  var cov_Uz_co2	:String = _
  var cov_Uz_h2o	:String = _
  var cov_Uz_Ts	:String = _
  var cov_Ux_Ux	:String = _
  var cov_Ux_Uy	:String = _
  var cov_Ux_co2	:String = _
  var cov_Ux_h2o	:String = _
  var cov_Ux_Ts	:String = _
  var cov_Uy_Uy	:String = _
  var cov_Uy_co2	:String = _
  var cov_Uy_h2o	:String = _
  var cov_Uy_Ts	:String = _
  var Ux_Avg	    :String = _
  var Uy_Avg	    :String = _
  var Uz_Avg	    :String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val originDF = in.read()

    val fluxDataCorrection = new FluxDataCorrectionUtil_2
    val df = fluxDataCorrection.DRCoordinateRotationUtil(spark,originDF
      ,Fc
      ,Le
      ,Hs
      ,u_star
      ,cov_Uz_Uz
      ,cov_Uz_Ux
      ,cov_Uz_Uy
      ,cov_Uz_co2
      ,cov_Uz_h2o
      ,cov_Uz_Ts
      ,cov_Ux_Ux
      ,cov_Ux_Uy
      ,cov_Ux_co2
      ,cov_Ux_h2o
      ,cov_Ux_Ts
      ,cov_Uy_Uy
      ,cov_Uy_co2
      ,cov_Uy_h2o
      ,cov_Uy_Ts
      ,Ux_Avg
      ,Uy_Avg
      ,Uz_Avg
    )

    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    Fc = MapUtil.get(map,"Fc").asInstanceOf[String]
    Le = MapUtil.get(map,"Le").asInstanceOf[String]
    Hs = MapUtil.get(map,"Hs").asInstanceOf[String]
    u_star =    MapUtil.get(map,"u_star").asInstanceOf[String]
    cov_Uz_Uz = MapUtil.get(map,"cov_Uz_Uz").asInstanceOf[String]
    cov_Uz_Ux = MapUtil.get(map,"cov_Uz_Ux").asInstanceOf[String]
    cov_Uz_Uy = MapUtil.get(map,"cov_Uz_Uy").asInstanceOf[String]
    cov_Uz_co2 = MapUtil.get(map,"cov_Uz_co2").asInstanceOf[String]
    cov_Uz_h2o = MapUtil.get(map,"cov_Uz_h2o").asInstanceOf[String]
    cov_Uz_Ts = MapUtil.get(map,"cov_Uz_Ts").asInstanceOf[String]
    cov_Ux_Ux = MapUtil.get(map,"cov_Ux_Ux").asInstanceOf[String]
    cov_Ux_Uy = MapUtil.get(map,"cov_Ux_Uy").asInstanceOf[String]
    cov_Ux_co2 = MapUtil.get(map,"cov_Ux_co2").asInstanceOf[String]
    cov_Ux_h2o = MapUtil.get(map,"cov_Ux_h2o").asInstanceOf[String]
    cov_Ux_Ts = MapUtil.get(map,"cov_Ux_Ts").asInstanceOf[String]
    cov_Uy_Uy = MapUtil.get(map,"cov_Uy_Uy").asInstanceOf[String]
    cov_Uy_co2 = MapUtil.get(map,"cov_Uy_co2").asInstanceOf[String]
    cov_Uy_h2o = MapUtil.get(map,"cov_Uy_h2o").asInstanceOf[String]
    cov_Uy_Ts = MapUtil.get(map,"cov_Uy_Ts").asInstanceOf[String]
    Ux_Avg    = MapUtil.get(map,"Ux_Avg").asInstanceOf[String]
    Uy_Avg    = MapUtil.get(map,"Uy_Avg").asInstanceOf[String]
    Uz_Avg    = MapUtil.get(map,"Uz_Avg").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val  Fc         =new PropertyDescriptor().name("Fc").displayName("Fc").description("CO2通量").defaultValue("Fc").required(true).example("Fc")
    val  Le         =new PropertyDescriptor().name("Le").displayName("Le").description("潜热通量").defaultValue("Le").required(true).example("Le")
    val  Hs         =new PropertyDescriptor().name("Hs").displayName("Hs").description("显热通量").defaultValue("Hs").required(true).example("Hs")
    val  u_star     =new PropertyDescriptor().name("u_star").displayName("u_star").description("摩擦风速").defaultValue("u_star").required(true).example("u_star")
    val  cov_Uz_Uz  =new PropertyDescriptor().name("cov_Uz_Uz").displayName("cov_Uz_Uz").description("垂直风速方差").defaultValue("cov_Uz_Uz").required(true).example("cov_Uz_Uz")
    val  cov_Uz_Ux  =new PropertyDescriptor().name("cov_Uz_Ux").displayName("cov_Uz_Ux").description("垂直风速与X方向风速协方差").defaultValue("cov_Uz_Ux").required(true).example("cov_Uz_Ux")
    val  cov_Uz_Uy  =new PropertyDescriptor().name("cov_Uz_Uy").displayName("cov_Uz_Uy").description("垂直风速与Y方向风速协方差").defaultValue("cov_Uz_Uy").required(true).example("cov_Uz_Uy")

    val  cov_Uz_co2 =new PropertyDescriptor().name("cov_Uz_co2").displayName("cov_Uz_co2").description("垂直风速与CO2密度协方差").defaultValue("cov_Uz_co2").required(true).example("cov_Uz_co2")
    val  cov_Uz_h2o =new PropertyDescriptor().name("cov_Uz_h2o").displayName("cov_Uz_h2o").description("垂直风速与H2O密度协方差").defaultValue("cov_Uz_h2o").required(true).example("cov_Uz_h2o")
    val  cov_Uz_Ts  =new PropertyDescriptor().name("cov_Uz_Ts").displayName("cov_Uz_Ts").description("垂直风速与温度协方差").defaultValue("cov_Uz_Ts").required(true).example("cov_Uz_Ts")
    val  cov_Ux_Ux  =new PropertyDescriptor().name("cov_Ux_Ux").displayName("cov_Ux_Ux").description("X方向风速方差").defaultValue("cov_Ux_Ux").required(true).example("cov_Ux_Ux")

    val  cov_Ux_Uy  =new PropertyDescriptor().name("cov_Ux_Uy").displayName("cov_Ux_Uy").description("X与Y方向风速协方差").defaultValue("cov_Ux_Uy").required(true).example("cov_Ux_Uy")
    val  cov_Ux_co2 =new PropertyDescriptor().name("cov_Ux_co2").displayName("cov_Ux_co2").description("X方向风速与CO2密度协方差").defaultValue("cov_Ux_co2").required(true).example("cov_Ux_co2")
    val  cov_Ux_h2o =new PropertyDescriptor().name("cov_Ux_h2o").displayName("cov_Ux_h2o").description("X方向风速与H2O密度协方差").defaultValue("cov_Ux_h2o").required(true).example("cov_Ux_h2o")
    val  cov_Ux_Ts  =new PropertyDescriptor().name("cov_Ux_Ts").displayName("cov_Ux_Ts").description("X方向风速与温度协方差").defaultValue("cov_Ux_Ts").required(true).example("cov_Ux_Ts")
    val  cov_Uy_Uy  =new PropertyDescriptor().name("cov_Uy_Uy").displayName("cov_Uy_Uy").description("Y方向风速方差").defaultValue("cov_Uy_Uy").required(true).example("cov_Uy_Uy")

    val  cov_Uy_co2 =new PropertyDescriptor().name("cov_Uy_co2").displayName("cov_Uy_co2").description("Y方向风速与CO2密度协方差").defaultValue("cov_Uy_co2").required(true).example("cov_Uy_co2")
    val  cov_Uy_h2o =new PropertyDescriptor().name("cov_Uy_h2o").displayName("cov_Uy_h2o").description("Y方向风速与H2O密度协方差").defaultValue("cov_Uy_h2o").required(true).example("cov_Uy_h2o")
    val  cov_Uy_Ts  =new PropertyDescriptor().name("cov_Uy_Ts").displayName("cov_Uy_Ts").description("Y方向风速与温度协方差").defaultValue("cov_Uy_Ts").required(true).example("cov_Uy_Ts")

    val  Ux_Avg     =new PropertyDescriptor().name("Ux_Avg").displayName("Ux_Avg").description("X方向平均风速").defaultValue("Ux_Avg").required(true).example("Ux_Avg")
    val  Uy_Avg     =new PropertyDescriptor().name("Uy_Avg").displayName("Uy_Avg").description("Y方向平均风速").defaultValue("Uy_Avg").required(true).example("Uy_Avg")
    val  Uz_Avg     =new PropertyDescriptor().name("Uz_Avg").displayName("Uz_Avg").description("Z方向平均风速").defaultValue("Uz_Avg").required(true).example("Uz_Avg")

    descriptor = Fc :: descriptor
    descriptor = Le :: descriptor
    descriptor = Hs :: descriptor
    descriptor = u_star :: descriptor

    descriptor = cov_Uz_Uz :: descriptor
    descriptor = cov_Uz_Ux :: descriptor
    descriptor = cov_Uz_Uy :: descriptor

    descriptor = cov_Uz_co2 :: descriptor
    descriptor = cov_Uz_h2o :: descriptor
    descriptor = cov_Uz_Ts :: descriptor
    descriptor = cov_Ux_Ux :: descriptor
    descriptor = cov_Ux_Uy :: descriptor

    descriptor = cov_Ux_co2 :: descriptor
    descriptor = cov_Ux_h2o :: descriptor
    descriptor = cov_Ux_Ts :: descriptor

    descriptor = cov_Uy_co2 :: descriptor
    descriptor = cov_Uy_h2o :: descriptor
    descriptor = cov_Uy_Ts :: descriptor
    descriptor = cov_Uy_Uy :: descriptor

    descriptor = Ux_Avg :: descriptor
    descriptor = Uy_Avg :: descriptor
    descriptor = Uz_Avg :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("png/Flux/flux.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List("Flux_dataCorrection")
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
