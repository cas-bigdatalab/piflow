package cn.piflow.bundle.flux.dataCorrection

import cn.piflow.bundle.flux.util.FluxDataCorrectionUtil_2
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class WplCorrection extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "WPL correction"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var Fc: String = _
  var Le: String = _
  var Hs: String = _

  var co2_Avg: String = _
  var h2o_Avg: String = _
  var Ts_Avg: String = _
  var rho_a_Avg: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val originDF = in.read()

    val fluxDataCorrection = new FluxDataCorrectionUtil_2
    val df = fluxDataCorrection.wplCorrectionUtil(spark,originDF
      ,Fc
      ,Le
      ,Hs
      ,co2_Avg
      ,h2o_Avg
      ,Ts_Avg
      ,rho_a_Avg
    )

    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    Fc = MapUtil.get(map,"Fc").asInstanceOf[String]
    Le = MapUtil.get(map,"Le").asInstanceOf[String]
    Hs = MapUtil.get(map,"Hs").asInstanceOf[String]
    co2_Avg = MapUtil.get(map,"co2_Avg").asInstanceOf[String]
    h2o_Avg = MapUtil.get(map,"h2o_Avg").asInstanceOf[String]
    Ts_Avg = MapUtil.get(map,"Ts_Avg").asInstanceOf[String]
    rho_a_Avg = MapUtil.get(map,"rho_a_Avg").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val  Fc         =new PropertyDescriptor().name("Fc").displayName("Fc").description("CO2通量").defaultValue("Fc").required(true).example("Fc")
    val  Le         =new PropertyDescriptor().name("Le").displayName("Le").description("潜热通量").defaultValue("Le").required(true).example("Le")
    val  Hs         =new PropertyDescriptor().name("Hs").displayName("Hs").description("显热通量").defaultValue("Hs").required(true).example("Hs")
    val  co2_Avg =new PropertyDescriptor().name("co2_Avg").displayName("co2_Avg").description("平均CO2密度").defaultValue("co2_Avg").required(true).example("co2_Avg")
    val  h2o_Avg =new PropertyDescriptor().name("h2o_Avg").displayName("h2o_Avg").description("平均H2O密度").defaultValue("h2o_Avg").required(true).example("h2o_Avg")
    val  Ts_Avg =new PropertyDescriptor().name("Ts_Avg").displayName("Ts_Avg").description("平均超声空气温度").defaultValue("Ts_Avg").required(true).example("Ts_Avg")
    val  rho_a_Avg =new PropertyDescriptor().name("rho_a_Avg").displayName("rho_a_Avg").description("平均空气密度").defaultValue("rho_a_Avg").required(true).example("rho_a_Avg")


    descriptor = Fc :: descriptor
    descriptor = Le :: descriptor
    descriptor = Hs :: descriptor

    descriptor = co2_Avg :: descriptor
    descriptor = h2o_Avg :: descriptor
    descriptor = Ts_Avg :: descriptor
    descriptor = rho_a_Avg :: descriptor


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
