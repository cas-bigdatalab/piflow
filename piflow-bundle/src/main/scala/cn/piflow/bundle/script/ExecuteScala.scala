package cn.piflow.bundle.script

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}

import scala.reflect.runtime.universe._
import scala.reflect.runtime.currentMirror
import scala.tools.reflect.ToolBox

import scala.reflect.macros.whitebox.Context
import scala.language.experimental.macros

class ExecuteScala extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Execute scala script"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var script : String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    script = MapUtil.get(map,"script").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val script = new PropertyDescriptor()
      .name("script")
      .displayName("script")
      .description("The code of scala")
      .defaultValue("")
      .required(true)
      .example("val t = 3 + 5 \n println(t)")
    //val execFunction = new PropertyDescriptor().name("execFunction").displayName("execFunction").description("The function of python script to be executed.").defaultValue("").required(true)
    descriptor = script :: descriptor
    //descriptor = execFunction :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/script/scala.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ScriptGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    import spark.implicits._

    val toolBox = currentMirror.mkToolBox()
    val result2 = evalCode[Unit](script)

  }

  private def evalCode[T](code : String) : T = {
    val toolBox = currentMirror.mkToolBox()
    toolBox.eval(toolBox.parse(code)).asInstanceOf[T]
  }
}
