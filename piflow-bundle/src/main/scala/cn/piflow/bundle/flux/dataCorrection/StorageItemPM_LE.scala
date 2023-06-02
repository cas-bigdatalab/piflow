package cn.piflow.bundle.flux.dataCorrection

import cn.piflow.bundle.flux.util.PM_LE
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
class StorageItemPM_LE extends ConfigurableStop{

  override val authorEmail: String = "rh@cnic.cn"
  override val description: String = "LE : Stored item correction by PMCheck"
  val inportList: List[String] = List("fluxCbsPort","metroCbsPort")
  override val outportList: List[String] = List(Port.DefaultPort)

  var equipmentHeightDifference:String = _
  var LE:String = _
  var everyPvaporFields: String = _
  var everyTaFields: String = _
  var time_interval:String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val fluxCBS = in.read("fluxCbsPort")
    val metroCBS = in.read("metroCbsPort")

    val pm = new PM_LE

//    val time_nterval = 1800
    val Lv: Double = 2440.0

    val arrayH = equipmentHeightDifference.split(",").map(_.toString.toDouble).toList
    val arrayLE = everyPvaporFields.split(",").map(_.toString).toList
    val arrayHS = everyTaFields.split(",").map(_.toString).toList
    val df = pm.calculateStoredItem(spark,fluxCBS,metroCBS,arrayH , LE, arrayLE, arrayHS, time_interval.toInt,Lv )

    out.write(df)
  }


  override def setProperties(map: Map[String, Any]): Unit = {

    equipmentHeightDifference = MapUtil.get(map, "equipmentHeightDifference").asInstanceOf[String]
    LE = MapUtil.get(map, "LE").asInstanceOf[String]
    everyPvaporFields = MapUtil.get(map, "everyPvaporFields").asInstanceOf[String]
    everyTaFields = MapUtil.get(map, "everyTaFields").asInstanceOf[String]
    time_interval = MapUtil.get(map, "time_interval").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()

    val equipmentHeightDifference = new PropertyDescriptor()
      .name("equipmentHeightDifference")
      .displayName("equipmentHeightDifference")
      .description("通量设备安装高度差：Height of each layer of contour line")
      .defaultValue("0.0, 1.0, 6.0, 4.0, 4.0, 8.0, 8.0")
      .required(true)
      .example("0.0, 1.0, 6.0, 4.0, 4.0, 8.0, 8.0")
    descriptor = equipmentHeightDifference :: descriptor

    val LE = new PropertyDescriptor()
      .name("LE")
      .displayName("LE")
      .description("LE flux field name")
      .defaultValue("LE")
      .required(true)
      .example("LE")
    descriptor = LE :: descriptor

    val everyPvaporFields = new PropertyDescriptor()
      .name("everyPvaporFields")
      .displayName("everyPvaporFields")
      .description("各层水汽压：H2O concentration of each layer")
      .defaultValue("Pvapor_1_AVG,Pvapor_2_AVG,Pvapor_3_AVG,Pvapor_4_AVG,Pvapor_5_AVG,Pvapor_6_AVG,Pvapor_7_AVG")
      .required(true)
      .example("")
    descriptor = everyPvaporFields :: descriptor

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
