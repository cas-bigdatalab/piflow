package cn.piflow.bundle.hdfs


import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import org.apache.spark.sql.SparkSession
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.FileSystem
import org.apache.hadoop.fs.Path


class DeleteHdfs extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.com"

  override val inportList: List[String] = List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)
  override val description: String = "Delete file or directory on hdfs"

  var hdfsUrl :String= _
  var deletePath :String = _
  var isCustomize:String=_
  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    if (isCustomize.equals("false")){
      val inDf = in.read()

      val configuration: Configuration = new Configuration()
      var pathStr: String =inDf.take(1)(0).get(0).asInstanceOf[String]
      val pathARR: Array[String] = pathStr.split("\\/")
      var hdfsUrl:String=""
      for (x <- (0 until 3)){
        hdfsUrl+=(pathARR(x) +"/")
      }
      configuration.set("fs.defaultFS",hdfsUrl)

      var fs: FileSystem = FileSystem.get(configuration)

      inDf.collect.foreach(row=>{
        pathStr = row.get(0).asInstanceOf[String]
        val path = new Path(pathStr)
        fs.delete(path,true)
      })

    } else {
      val array = deletePath.split(",")

      for (i<- 0 until array.length){
        val hdfsPath = hdfsUrl+"/"+array(i)
        val path = new Path(hdfsPath)

        val config = new Configuration()
        config.set("fs.defaultFS",hdfsUrl)
        val fs = FileSystem.get(config)

        fs.delete(path,true)
      }
    }
  }
  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    deletePath = MapUtil.get(map,key="deletePath").asInstanceOf[String]
    isCustomize=MapUtil.get(map,key="isCustomize").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfsUrl = new PropertyDescriptor().name("hdfsUrl").displayName("hdfsUrl").defaultValue("").required(true)
    val deletePath = new PropertyDescriptor().name("deletePath").displayName("deletePath").defaultValue("").required(true)
    val isCustomize = new PropertyDescriptor().name("isCustomize").displayName("isCustomize").description("Whether to customize the compressed file path, if true, " +
      "you must specify the path where the compressed file is located . " +
      "If it is false, it will automatically find the file path data from the upstream port ")
      .defaultValue("false").allowableValues(Set("true","false")).required(true)
    descriptor = isCustomize :: descriptor
    descriptor = hdfsUrl :: descriptor
    descriptor = deletePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/DeleteHdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
