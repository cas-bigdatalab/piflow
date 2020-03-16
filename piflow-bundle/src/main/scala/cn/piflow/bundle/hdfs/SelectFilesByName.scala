package cn.piflow.bundle.hdfs

import java.util.regex.Pattern

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileStatus, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

import scala.collection.mutable.ArrayBuffer

class SelectFilesByName extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Select files by file name"
  override val inportList: List[String] = List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)

  var HDFSUrl:String=_
  var HDFSPath:String=_
  var selectionConditions:String =_

  var fs: FileSystem=null
  var pathARR:ArrayBuffer[String]=ArrayBuffer()
  var selectArr:Array[String]=null

  def selectFile(path: String): Unit = {
    val statusesARR: Array[FileStatus] = fs.listStatus(new Path(path))
    for(each <- statusesARR){
      val pathStr = each.getPath.toString
      if(each.isFile){
        val fileName: String = pathStr.split("/").last
        selectArr = selectionConditions.split(",")
        var b: Boolean =false
        for(x <- selectArr){
          b = Pattern.matches(x,fileName)
          if(b){
            pathARR += pathStr
          }
        }
      }else{
        selectFile(pathStr)
      }
    }
  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val session: SparkSession = pec.get[SparkSession]()

    val configuration: Configuration = new Configuration()
    configuration.set("fs.defaultFS", HDFSUrl)
    fs = FileSystem.get(configuration)

    selectFile(HDFSPath)

    val rows: List[Row] = pathARR.map(each => {
      var arr:Array[String]=Array(each)
      val row: Row = Row.fromSeq(arr)
      row
    }).toList
    val rowRDD: RDD[Row] = session.sparkContext.makeRDD(rows)
    val fields: Array[StructField] = "path".split("/").map(d=>StructField(d,StringType,nullable = true))
    val schema: StructType = StructType(fields)
    val df: DataFrame = session.createDataFrame(rowRDD,schema)

    println("#################################################")
    df.show(20)
    println(df.count+"#################################################")



    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    HDFSUrl=MapUtil.get(map,key="HDFSUrl").asInstanceOf[String]
    HDFSPath=MapUtil.get(map,key="HDFSPath").asInstanceOf[String]
    selectionConditions=MapUtil.get(map,key="selectionConditions").asInstanceOf[String]
  }


  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val HDFSUrl = new PropertyDescriptor().name("HDFSUrl").displayName("HDFSUrl").description("The URL of the HDFS file system, such as hdfs://ip:port")
      .defaultValue("hdfs://").required(true)
    val HDFSPath = new PropertyDescriptor().name("HDFSPath").displayName("HDFSPath").description("The save path of the HDFS file system, such as /test/Ab")
      .defaultValue("").required(true)
    val selectionConditions = new PropertyDescriptor().name("selectionConditions").displayName("selectionConditions").description("To select conditions, you need to fill in regular expressions in java, such as. * abc. *")
      .defaultValue("").required(true)
    descriptor = HDFSUrl :: descriptor
    descriptor = HDFSPath :: descriptor
    descriptor = selectionConditions :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/SelectFileByName.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
