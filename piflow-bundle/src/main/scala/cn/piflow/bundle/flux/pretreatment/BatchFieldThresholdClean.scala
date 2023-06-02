package cn.piflow.bundle.flux.pretreatment

import cn.piflow.bundle.flux.util.FluxUtil_1
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class BatchFieldThresholdClean extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Batch field threshold cleaning,Include upper and lower limits: The schema of the threshold table must be included 'field','min_value' ,'max_value','flag_value'"
//  override val inportList: List[String] =List(Port.LeftPort,Port.RightPort)
  override val inportList: List[String] =List("MasterTablePort","ThresholdTablePort")
  val outportList: List[String] = List(Port.DefaultPort)


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val MasterDF =  in.read("MasterTablePort")
    val ThresholdDF = in.read("ThresholdTablePort")
    val flux = new FluxUtil_1
    val df = flux.batchFieldThresholdCleaning(spark,MasterDF,ThresholdDF)

    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

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
