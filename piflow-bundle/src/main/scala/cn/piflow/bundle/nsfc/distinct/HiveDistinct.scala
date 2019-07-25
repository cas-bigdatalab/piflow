package cn.piflow.bundle.nsfc.distinct

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import org.apache.spark.sql.SparkSession

class HiveDistinct  extends ConfigurableStop{
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = ""
  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)
//  val primaryKey:String = _
//  val subPrimaryKey:String = _
//  val idKeyName : String = _
//  val processKey = _
//  val timeFields = _
//  val subTimeFields = _
  var tableName : String = _ //after wash
  var noChangeSource : String = _
  var sourceField : String = _
  var timeField : String = _
  var noChange : Boolean = _
  var baseOnTime : Boolean = _
  var baseOnField : Boolean = _
  var distinctRule : String = _
  var distinctFields : String = _
  //  val subTableName = _
  override def setProperties(map: Map[String, Any]): Unit = ???

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] =   ImageUtil.getImage("icon/hive/SelectHiveQL.png")

  override def getGroup(): List[String] = {
    List(StopGroup.NSFC.toString, "sha0w", "distinct")
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    if (noChange){
      out.write(in.read())
      return
    }
    val spark = pec.get[SparkSession]()
  }
}
