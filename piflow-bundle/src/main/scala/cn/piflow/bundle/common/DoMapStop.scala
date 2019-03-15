package cn.piflow.bundle.common

import cn.piflow.conf._
import cn.piflow.lib._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.util. ScriptEngine
import cn.piflow._
import cn.piflow.lib.io.{FileFormat, TextFile}
import org.apache.spark.sql.types.StructType



class DoMapStop extends ConfigurableStop{


  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "DoMap stop."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var  targetSchema: StructType = null
  var  SCRIPT: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    in.read().show()

    val doMap = new  DoMap(ScriptEngine.logic(SCRIPT))
    doMap.perform(in,out,pec)


  }

  def createCountWords() = {

    val processCountWords = new FlowImpl();
    processCountWords.addStop("LoadStream", new LoadStream(TextFile("hdfs://10.0.86.89:9000/yg/2", FileFormat.TEXT)));
    processCountWords.addStop("DoMap", new DoMapStop);

    processCountWords.addPath(Path.from("LoadStream").to("DoMap"));

    new FlowAsStop(processCountWords);
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    SCRIPT = MapUtil.get(map,"SCRIPT_1").asInstanceOf[String]

  }
  override def initialize(ctx: ProcessContext): Unit = {

  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val SCRIPT = new PropertyDescriptor().name("SCRIPT").displayName("SCRIPT").description("").defaultValue("").required(true)
    descriptor = SCRIPT :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/DoMap.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }



}



