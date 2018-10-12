package cn.piflow.bundle.json

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.SparkSession

class JsonStringParser extends ConfigurableStop{
  val authorEmail: String = "xjzhu@cnic.cn"
  val inportCount: Int = 1
  val outportCount: Int = 1

  var jsonString: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val jsonRDD = spark.sparkContext.makeRDD(jsonString :: Nil)
    val jsonDF = spark.read.json(jsonRDD)

    jsonDF.show(10)
    out.write(jsonDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    jsonString = MapUtil.get(map,"jsonString").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.JsonGroup.toString)
  }


}
