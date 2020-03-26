package cn.piflow.bundle.hdfs

import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileStatus, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

import scala.collection.mutable.ArrayBuffer



class ListHdfs extends ConfigurableStop{

  override val authorEmail: String = "ygang@cnic.com"
  override val description: String = "Retrieve a list of files from hdfs"
  override val inportList: List[String] = List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)

  var hdfsPath :String= _
  var hdfsUrl :String= _
  var pathARR:ArrayBuffer[String]=ArrayBuffer()

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext

    val path = new Path(hdfsPath)
    iterationFile(path.toString)

    val rows: List[Row] = pathARR.map(each => {
      var arr:Array[String]=Array(each)
      val row: Row = Row.fromSeq(arr)
      row
    }).toList

    val rowRDD: RDD[Row] = sc.makeRDD(rows)

    val schema: StructType = StructType(Array(
      StructField("path",StringType)
    ))
    val outDF: DataFrame = spark.createDataFrame(rowRDD,schema)
    out.write(outDF)
  }

  // recursively traverse the folder
  def iterationFile(path: String):Unit = {
    val config = new Configuration()
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)
    val listf = new Path(path)

    val statuses: Array[FileStatus] = fs.listStatus(listf)

    for (f <- statuses) {
      val fsPath = f.getPath().toString
      if (f.isDirectory) {
        iterationFile(fsPath)
      } else{
        pathARR += f.getPath.toString
      }
    }

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsPath = MapUtil.get(map,key="hdfsPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfsPath = new PropertyDescriptor()
      .name("hdfsPath")
      .displayName("HdfsPath")
      .defaultValue("")
      .description("File path of HDFS")
      .required(true)
      .example("/work/")
    descriptor = hdfsPath :: descriptor

    val hdfsUrl = new PropertyDescriptor()
      .name("hdfsUrl")
      .displayName("HdfsUrl")
      .defaultValue("")
      .description("URL address of HDFS")
      .required(true)
      .example("hdfs://192.168.3.138:8020")

    descriptor = hdfsUrl :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/ListHdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
