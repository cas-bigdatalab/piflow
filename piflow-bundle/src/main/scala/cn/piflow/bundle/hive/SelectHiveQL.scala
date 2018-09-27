package cn.piflow.bundle.hive

import cn.piflow._
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, HiveGroup, StopGroup, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

import scala.beans.BeanProperty



class SelectHiveQL extends ConfigurableStop {

  val authorEmail: String = "xjzhu@cnic.cn"
  val inportCount: Int = 0
  val outportCount: Int = 1

  var hiveQL:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    import spark.sql
    val df = sql(hiveQL)
    df.show()

    out.write(df)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    hiveQL = MapUtil.get(map,"hiveQL").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hiveQL = new PropertyDescriptor().name("hiveQL").displayName("HiveQL").defaultValue("").allowableValues(Set("")).required(true)
    descriptor = hiveQL :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/selectHiveQL.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.HiveGroup.toString)
  }


}


