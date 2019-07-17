package cn.piflow.bundle.nsfc.distinct

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import org.apache.spark.sql.SparkSession

class HiveTableMergeOn extends ConfigurableStop{
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = ""
  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  override def setProperties(map: Map[String, Any]): Unit = ???

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = ImageUtil.getImage("icon/hive/SelectHiveQL.png")

  override def getGroup(): List[String] =  List(StopGroup.NSFC.toString, "sha0w", "distinct")

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
  }
}
