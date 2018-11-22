package cn.piflow.bundle.hdfs


import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import org.apache.spark.sql.SparkSession
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.FileSystem
import org.apache.hadoop.fs.Path


class DeleteHdfs extends ConfigurableStop{
  override val authorEmail: String = "ygang@cmic.com"

  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
  override val description: String = "delete file or dir from hdfs"

  var hdfsUrl :String= _
  var deletePath :String = _
  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    val array = deletePath.split(",")

    for (i<- 0 until array.length){
      val hdfsPath = hdfsUrl+array(i)
      val path = new Path(array(i))

      val config = new Configuration()
      config.set("fs.defaultFS",hdfsUrl)
      val fs = FileSystem.get(config)

      println(path+"ddddddddddddddddddd--delete")
      fs.delete(path,true)

//      if (fs.isDirectory(path)){
//        println("-------wenjianjia-----")
//              fs.delete(path,true)
//      }
//
//      else if(fs.isFile(path)){
//        println("wenjian -------------------------")
//              fs.delete(path,true)
//      } else {
//        fs.delete(path, true)
//      }
    }
  }
  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    deletePath = MapUtil.get(map,key="deletePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfsUrl = new PropertyDescriptor().name("hdfsUrl").displayName("hdfsUrl").defaultValue("").required(true)
    val deletePath = new PropertyDescriptor().name("deletePath").displayName("deletePath").defaultValue("").required(true)
    descriptor = hdfsUrl :: descriptor
    descriptor = deletePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("hdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.HdfsGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
