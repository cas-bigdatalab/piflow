package cn.piflow.bundle.json

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

class JsonStringParser extends ConfigurableStop{
  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Parse json string"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var jsonString: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val jsonRDD = spark.sparkContext.makeRDD(jsonString :: Nil)
    val jsonDF = spark.read.json(jsonRDD)
    out.write(jsonDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    jsonString = MapUtil.get(map,"jsonString").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val jsonString = new PropertyDescriptor()
      .name("jsonString")
      .displayName("JsonString")
      .description("The json string")
      .defaultValue("")
      .required(true)
      .example("{\"id\":\"13\",\"name\":\"13\",\"score\":\"13\",\"school\":\"13\",\"class\":\"13\"}")

    descriptor = jsonString :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/json/JsonStringParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JsonGroup)
  }


}
