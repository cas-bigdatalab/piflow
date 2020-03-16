package cn.piflow.bundle.file

import java.io.{ByteArrayOutputStream, InputStream}
import java.net.{HttpURLConnection, URI, URL}

import org.apache.hadoop.fs.FileSystem
import org.apache.hadoop.fs.Path
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.hadoop.conf.Configuration
import org.apache.spark.sql.SparkSession

class PutFile extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Put local file to hdfs"
  val inportList: List[String] = List(Port.DefaultPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)
  var hdfs_path:String =_
  var local_path:String=_
  var fs:FileSystem=null

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    initFs(hdfs_path)
    addFiletoHDFS(hdfs_path,local_path)
  }

  def initFs(uri:String):Unit={
    val conf:Configuration=new Configuration()
    fs= FileSystem.get(new URI(uri),conf)
  }

  def addFiletoHDFS(hdfs_path:String,local_path:String):Unit={
    val dst:Path=new Path(hdfs_path)
    val src:Path=new Path(local_path)
    fs.copyFromLocalFile(src,dst)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    hdfs_path=MapUtil.get(map,key="hdfs_path").asInstanceOf[String]
    local_path=MapUtil.get(map,key="local_path").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfs_path = new PropertyDescriptor().name("hdfs_path").displayName("HDFS_PATH").defaultValue("").required(true)
    val local_path = new PropertyDescriptor().name("local_path").displayName("LOCAL_PATH").defaultValue("").required(true)
    descriptor = hdfs_path :: descriptor
    descriptor = local_path :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/file/PutFile.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.FileGroup.toString)
  }


}
