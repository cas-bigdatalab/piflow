package cn.piflow.bundle.flux.dataCorrection

import cn.piflow.bundle.flux.util.PM_HS
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

/**
 * 存储项校正计算，廓线法(PMCheck)利用配 套的廓线系统获取的分层 CO2、H2O 浓度、温度数据计算存储项
 *
 * @Author renhao
 * @Description:
 * @Data 2023/2/27 16:08
 * @Modified By:
 */
class StorageItemPM_Hs extends ConfigurableStop{

  override val authorEmail: String = "rh@cnic.cn"
  override val description: String = "Hs : Stored item correction by PMCheck"
  val inportList: List[String] = List("fluxCbsPort","metroCbsPort")
  override val outportList: List[String] = List(Port.DefaultPort)

  var equipmentHeightDifference:String = _
  var Hs:String = _
  var everyTaFields: String = _
  var time_interval:String = _
  var rho_a_Avg :String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val fluxCBS = in.read("fluxCbsPort")
    val metroCBS = in.read("metroCbsPort")

    val pm = new PM_HS

//    val time_nterval = 1800
    val CP: Double = 1004.67

    val arrayH = equipmentHeightDifference.split(",").map(_.toString.toDouble).toList
    val arrayHS = everyTaFields.split(",").map(_.toString).toList
    val df = pm.calculateStoredItem(spark,fluxCBS,metroCBS,arrayH , Hs, arrayHS, time_interval.toInt,CP,rho_a_Avg )

    out.write(df)
  }


  override def setProperties(map: Map[String, Any]): Unit = {

    equipmentHeightDifference = MapUtil.get(map, "equipmentHeightDifference").asInstanceOf[String]
    Hs = MapUtil.get(map, "Hs").asInstanceOf[String]
    everyTaFields = MapUtil.get(map, "everyTaFields").asInstanceOf[String]
    time_interval = MapUtil.get(map, "time_interval").asInstanceOf[String]
    rho_a_Avg = MapUtil.get(map, "rho_a_Avg").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()

    val equipmentHeightDifference = new PropertyDescriptor()
      .name("equipmentHeightDifference")
      .displayName("equipmentHeightDifference")
      .description("通量设备安装高度差,自第一层开始：Height of each layer of contour line")
      .defaultValue("0.0, 1.0, 6.0, 4.0, 4.0, 8.0, 8.0")
      .required(true)
      .example("0.0, 1.0, 6.0, 4.0, 4.0, 8.0, 8.0")
    descriptor = equipmentHeightDifference :: descriptor

    val Hs = new PropertyDescriptor()
      .name("Hs")
      .displayName("Hs")
      .description("Hs flux field name")
      .defaultValue("Hs")
      .required(true)
      .example("Hs")
    descriptor = Hs :: descriptor

    val rho_a_Avg = new PropertyDescriptor()
      .name("rho_a_Avg")
      .displayName("rho_a_Avg")
      .description("平均空气密度：rho_a_Avg")
      .defaultValue("rho_a_Avg")
      .required(true)
      .example("")
    descriptor = rho_a_Avg :: descriptor

    val everyTaFields = new PropertyDescriptor()
      .name("everyTaFields")
      .displayName("everyTaFields")
      .description("各层平均温度：temperature concentration of each layer")
      .defaultValue("Ta_1_AVG,Ta_2_AVG,Ta_3_AVG,Ta_4_AVG,Ta_5_AVG,Ta_6_AVG,Ta_7_AVG")
      .required(true)
      .example("")
    descriptor = everyTaFields :: descriptor

    val time_interval = new PropertyDescriptor()
      .name("time_interval")
      .displayName("time_interval")
      .description("time interval")
      .defaultValue("1800")
      .required(true)
      .example("1800")
    descriptor = time_interval :: descriptor

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
