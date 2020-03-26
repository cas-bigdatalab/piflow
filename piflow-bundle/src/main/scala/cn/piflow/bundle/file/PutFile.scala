package cn.piflow.bundle.file

import cn.piflow.bundle.util.RemoteShellExecutor
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession


class PutFile extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Upload local files to hdfs"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var IP :String= _
  var User :String= _
  var PassWord :String = _
  var localFile:String =_
  var hdfsPath:String =_


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark: SparkSession = pec.get[SparkSession]()


    val executor: RemoteShellExecutor = new RemoteShellExecutor(IP,User,PassWord)

    executor.exec(s"hdfs dfs -put ${localFile}  ${hdfsPath}")


  }


  def setProperties(map : Map[String, Any]): Unit = {
    IP = MapUtil.get(map,key="IP").asInstanceOf[String]
    User = MapUtil.get(map,key="User").asInstanceOf[String]
    PassWord = MapUtil.get(map,key="PassWord").asInstanceOf[String]
    localFile = MapUtil.get(map,key="localFile").asInstanceOf[String]
    hdfsPath = MapUtil.get(map,key="hdfsPath").asInstanceOf[String]


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


    val hdfsPath = new PropertyDescriptor()
      .name("hdfsPath")
      .displayName("HdfsPath")
      .description("path to folder on hdfs")
      .defaultValue("")
      .required(true)
      .example("/work/")


    val localFile = new PropertyDescriptor()
      .name("localFile")
      .displayName("LocalFile")
      .description("Path to the local server file")
      .defaultValue("")
      .required(true)
      .example("/opt/test.csv")



    descriptor = IP :: descriptor
    descriptor = User :: descriptor
    descriptor = PassWord :: descriptor
    descriptor = hdfsPath :: descriptor
    descriptor = localFile :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/file/PutFile.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.FileGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = { }

}

