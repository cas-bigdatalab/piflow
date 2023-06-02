package cn.piflow.bundle.flux.pretreatment

import cn.piflow.bundle.flux.util.FluxUtil_1
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class AddDayID extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "按照year、month、day、hour 添加自增id，且根据year、month、day添加 day_id,"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var partitionNum: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

//    val partitionNum = in.read().rdd.getNumPartitions

    val flux = new FluxUtil_1
    val df = flux.AddIdWithDay(spark, in.read(),partitionNum.toInt)

    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    partitionNum = MapUtil.get(map,"partitionNum").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val partitionNum = new PropertyDescriptor()
      .name("partitionNum")
      .displayName("partitionNum")
      .description("Set the number of partitions")
      .defaultValue("20")
      .required(true)
      .example("20")
    descriptor = partitionNum :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("png/Flux/flux.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List("Flux_pretreatment")
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
