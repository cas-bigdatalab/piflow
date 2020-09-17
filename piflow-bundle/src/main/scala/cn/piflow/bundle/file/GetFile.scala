package cn.piflow.bundle.file

import cn.piflow.bundle.util.RemoteShellExecutor
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession


class GetFile extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Download fields from hdfs to local"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var IP :String= _
  var User :String= _
  var PassWord :String = _
  var hdfsFile:String =_
  var localPath:String =_


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark: SparkSession = pec.get[SparkSession]()


    val executor: RemoteShellExecutor = new RemoteShellExecutor(IP,User,PassWord)

    executor.exec(s"hdfs dfs -get ${hdfsFile}  ${localPath}")

  }


  def setProperties(map : Map[String, Any]): Unit = {
    IP = MapUtil.get(map,key="IP").asInstanceOf[String]
    User = MapUtil.get(map,key="User").asInstanceOf[String]
    PassWord = MapUtil.get(map,key="PassWord").asInstanceOf[String]
    hdfsFile = MapUtil.get(map,key="hdfsFile").asInstanceOf[String]
    localPath = MapUtil.get(map,key="localPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val IP = new PropertyDescriptor()
      .name("IP")
      .displayName("IP")
      .description("Server IP where the local file is located")
      .defaultValue("")
      .required(true)
      .example("127.0.0.1")
    descriptor = IP :: descriptor

    val User = new PropertyDescriptor()
      .name("User")
      .displayName("User")
      .description("Server User where the local file is located")
      .defaultValue("root")
      .required(true)
      .example("root")
    descriptor = User :: descriptor

    val PassWord = new PropertyDescriptor()
      .name("PassWord")
      .displayName("PassWord")
      .description("Password of the server where the local file is located")
      .defaultValue("")
      .required(true)
      .example("123456")
    descriptor = PassWord :: descriptor

    val hdfsFile = new PropertyDescriptor()
      .name("hdfsFile")
      .displayName("HdfsFile")
      .description("path to file on hdfs")
      .required(true)
      .example("/work/test.csv")
    descriptor = hdfsFile :: descriptor

    val localPath = new PropertyDescriptor()
      .name("localPath")
      .displayName("LocalPath")
      .description("Local folder")
      .defaultValue("")
      .required(true)
      .example("/opt/")
    descriptor = localPath :: descriptor


    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/file/FetchFile.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.FileGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = { }

}

