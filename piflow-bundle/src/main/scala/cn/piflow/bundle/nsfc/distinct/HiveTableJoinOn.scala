package cn.piflow.bundle.nsfc.distinct

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

class HiveTableJoinOn extends ConfigurableStop{
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = ""
  override val inportList: List[String] = List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)

  var baseTableName : String = _
  var subTableName : String = _
  var joinField : Seq[String] = _
  var joinForm : String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    baseTableName = MapUtil.get(map,"baseTable").asInstanceOf[String]
    subTableName = MapUtil.get(map,"subTable").asInstanceOf[String]
    joinField = MapUtil.get(map,"joinFields").asInstanceOf[String].split(";")
    joinForm = MapUtil.get(map,"joinForm").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val baseTableName = new PropertyDescriptor().
      name("baseTable").
      displayName("left table name").
      description("the left table you join on").
      defaultValue("temp.t_person").
      required(true)
    descriptor = baseTableName :: descriptor

    val subTableName = new PropertyDescriptor().
      name("subTable").
      displayName("right table name").
      description("the right table you join on").
      defaultValue("origin.o_person_sub_full").
      required(true)
    descriptor = subTableName :: descriptor

    val joinFields = new PropertyDescriptor().
      name("joinFields").
      displayName("join field").
      description("the fields you join on, split by ';'").
      defaultValue("psn_code").
      required(true)
    descriptor = joinFields :: descriptor

    val joinForm = new PropertyDescriptor().
      name("joinForm").
      displayName("join form").
      description("the way you join on").
      defaultValue("left_outer").
      required(true).
      allowableValues(Set("inner", "outer", "left_outer", "right_outer", "leftsemi"))
    descriptor = joinForm :: descriptor


    descriptor
  }

  override def getIcon(): Array[Byte] = ImageUtil.getImage("icon/hive/SelectHiveQL.png")

  override def getGroup(): List[String] =  List(StopGroup.NSFC.toString, "sha0w", "distinct")

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val subTable = spark.read.table(subTableName)
    val ot = spark.read.table(baseTableName).join(subTable, joinField, joinForm)
    out.write(ot)
  }
}
