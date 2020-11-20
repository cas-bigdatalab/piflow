package cn.piflow.bundle.script

import cn.piflow.bundle.util.RemoteShellExecutor
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession


class ExecuteShell extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Execute shell script"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var IP :String= _
  var User :String= _
  var PassWord :String = _
  var shellString:String =_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val executor: RemoteShellExecutor = new RemoteShellExecutor(IP,User,PassWord)
    val strings: Array[String] = shellString.split("###")
    strings.foreach(x=>{
      executor.exec(x.toString)
    })
  }


  def setProperties(map : Map[String, Any]): Unit = {
    IP = MapUtil.get(map,key="IP").asInstanceOf[String]
    User = MapUtil.get(map,key="User").asInstanceOf[String]
    PassWord = MapUtil.get(map,key="PassWord").asInstanceOf[String]
    shellString = MapUtil.get(map,key="shellString").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val IP = new PropertyDescriptor()
      .name("IP")
      .displayName("IP")
      .description("Server IP where the local file is located")
      .defaultValue("")
      .required(true)
      .description("192.168.3.139")

    val User = new PropertyDescriptor()
      .name("User")
      .displayName("User")
      .description("Server User where the local file is located")
      .defaultValue("root")
      .required(true)
      .example("root")

    val PassWord = new PropertyDescriptor()
      .name("PassWord")
      .displayName("PassWord")
      .description("Password of the server where the local file is located")
      .defaultValue("")
      .required(true)
      .example("123456")

    val shellString = new PropertyDescriptor()
      .name("shellString")
      .displayName("ShellString")
      .description("shell script, multiple sentences separated by ###")
      .defaultValue("")
      .required(true)
      .example("mkdir /work/###cp /opt/1.29.3.tar.gz /work/")
      .language(Language.Shell)


    descriptor = IP :: descriptor
    descriptor = User :: descriptor
    descriptor = PassWord :: descriptor
    descriptor = shellString :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/script/ShellExecutor.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ScriptGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = { }

}

