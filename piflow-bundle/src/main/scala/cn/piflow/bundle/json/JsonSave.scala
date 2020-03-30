package cn.piflow.bundle.json

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SaveMode

import scala.beans.BeanProperty

class JsonSave extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Save data into json file"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var jsonSavePath: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val jsonDF = in.read()
    jsonDF.write.format("json").mode(SaveMode.Overwrite).save(jsonSavePath)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    jsonSavePath = MapUtil.get(map,"jsonSavePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val jsonSavePath = new PropertyDescriptor()
      .name("jsonSavePath")
      .displayName("JsonSavePath")
      .description("The save path of the json file")
      .defaultValue("")
      .required(true)
        .example("hdfs://192.168.3.138:8020/work/testJson/test/")

    descriptor = jsonSavePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/json/JsonSave.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JsonGroup)
  }


}
