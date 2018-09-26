package cn.piflow.bundle.xml

import cn.piflow._
import cn.piflow.conf.{ConfigurableStop, StopGroup, StopGroupEnum, XmlGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.types.StructType

import scala.beans.BeanProperty

class XmlParser extends ConfigurableStop {

  val authorEmail: String = "xjzhu@cnic.cn"
  val inportCount: Int = 1
  val outportCount: Int = 1

  var xmlpath:String = _
  var rowTag:String = _
  var schema: StructType = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    val xmlDF = spark.read.format("com.databricks.spark.xml")
      .option("rowTag",rowTag)
      .option("treatEmptyValuesAsNulls",true)
      /*.schema(schema)*/
      .load(xmlpath)

    /*xmlDF.select("ee").rdd.collect().foreach( row =>
      println(row.toSeq)
    )*/
    xmlDF.show(30)
    out.write(xmlDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    xmlpath = MapUtil.get(map,"xmlpath").asInstanceOf[String]
    rowTag = MapUtil.get(map,"rowTag").asInstanceOf[String]
    schema = null
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.XmlGroup.toString)
  }

}
