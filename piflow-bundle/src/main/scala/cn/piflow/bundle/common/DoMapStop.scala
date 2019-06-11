package cn.piflow.bundle.common

import cn.piflow.conf._
import cn.piflow.lib._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.util.ScriptEngine
import cn.piflow._
import org.apache.spark.sql.types.{StringType, StructField, StructType}



class DoMapStop extends ConfigurableStop{


  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Do map"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var  schema: String = _
  var  SCRIPT: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {


    val fieldsArray: Array[String] = schema.split(",")
    val fields = fieldsArray.map(x => {
      StructField(x, StringType, nullable = true)
    })
    val targetSchema = StructType(fields)

    val doMap = new  DoMap(ScriptEngine.logic(SCRIPT),targetSchema)
    doMap.perform(in,out,pec)

 }

  override def setProperties(map: Map[String, Any]): Unit = {
    SCRIPT = MapUtil.get(map,"SCRIPT").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]

  }
  override def initialize(ctx: ProcessContext): Unit = {

  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val SCRIPT = new PropertyDescriptor().name("SCRIPT").displayName("SCRIPT").description("").defaultValue("").required(true)
    descriptor = SCRIPT :: descriptor
    val schema = new PropertyDescriptor().name("schema").displayName("schema").description("").defaultValue("").required(true)
    descriptor = schema :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/DoMapStop.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }



}




