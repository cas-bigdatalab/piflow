package cn.piflow.bundle.hdfs

import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileStatus, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

import scala.collection.mutable.ArrayBuffer



class ListHdfs extends ConfigurableStop{
  override val authorEmail: String = "ygang@cmic.com"

  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val description: String = "Retrieve a list of files from hdfs"

  var HDFSPath :String= _
  var HDFSUrl :String= _
  var pathARR:ArrayBuffer[String]=ArrayBuffer()
  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext

    val path = new Path(HDFSPath)
    iterationFile(path.toString)

    import spark.implicits._

    val rows: List[Row] = pathARR.map(each => {
      var arr:Array[String]=Array(each)
      val row: Row = Row.fromSeq(arr)
      row
    }).toList

    val rowRDD: RDD[Row] = sc.makeRDD(rows)
//    val fields: Array[StructField] = "path".split("/").map(d=>StructField(d,StringType,nullable = true))
//    val schema: StructType = StructType(fields)

    val schema: StructType = StructType(Array(
      StructField("path",StringType)
    ))
    val outDF: DataFrame = spark.createDataFrame(rowRDD,schema)
    out.write(outDF)
  }

  // recursively traverse the folder
  def iterationFile(path: String):Unit = {
    val config = new Configuration()
    config.set("fs.defaultFS",HDFSUrl)
    val fs = FileSystem.get(config)
    val listf = new Path(path)

    val statuses: Array[FileStatus] = fs.listStatus(listf)

    for (f <- statuses) {
      val fsPath = f.getPath().toString
      if (f.isDirectory) {
//        pathARR += fsPath
        iterationFile(fsPath)
      } else{
        pathARR += f.getPath.toString
      }
    }

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    HDFSUrl = MapUtil.get(map,key="HDFSUrl").asInstanceOf[String]
    HDFSPath = MapUtil.get(map,key="HDFSPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfsPath = new PropertyDescriptor().name("HDFSPath").displayName("HDFSPath").defaultValue("").required(true)
    val hdfsUrl = new PropertyDescriptor().name("HDFSUrl").displayName("HDFSUrl").defaultValue("").required(true)
    descriptor = hdfsPath :: descriptor
    descriptor = hdfsUrl :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/ListHdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
