package cn.piflow.bundle.json


import java.net.URI

import cn.piflow.bundle.util.JsonUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileStatus, FileSystem, FileUtil, Path}
import org.apache.spark.sql._

import scala.collection.mutable.ArrayBuffer
import scala.util.control.Breaks.{break, breakable}
import org.apache.spark.sql.{DataFrame, SQLContext}



class FolderJsonParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val description: String ="Parse json folder"

  var FolderPath:String = _
  var tag : String = _

  var openArrField:String=""
  var ArrSchame:String=""
  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sql: SQLContext = spark.sqlContext

    val arrPath: ArrayBuffer[String] = getFileName(FolderPath)
    var FinalDF: DataFrame = getFinalDF(arrPath,sql)

    if(tag.length>0){
      val writeDF: DataFrame = JsonUtil.ParserJsonDF(FinalDF,tag)
      FinalDF=writeDF
    }

    out.write(FinalDF)
  }

  def getDf(Path: String,ss:SQLContext): DataFrame ={
    val frame: DataFrame = ss.read.json(Path)
    frame
  }

  def getFinalDF(arrPath: ArrayBuffer[String],ss:SQLContext): DataFrame = {
    var index: Int = 0
    breakable {
      for (i <- 0 until arrPath.length) {
        if (getDf(arrPath(i), ss).count() != 0) {
          index = i
          break
        }
      }
    }

    val df01 = ss.read.option("multiline","true").json(arrPath(index))

    var aaa:String="name"
    var df: DataFrame = df01
    for(d <- index+1 until(arrPath.length)){
      if(getDf(arrPath(d),ss).count()!=0){
                val df1: DataFrame = ss.read.option("multiline","true").json(arrPath(d))
        val df2: DataFrame = df.union(df1).toDF()
        df=df2
      }
    }
    df
  }


  def getFileName(path:String):ArrayBuffer[String]={
    val conf: Configuration = new Configuration()
    val hdfs: FileSystem = FileSystem.get(URI.create(path),conf)
    val fs: Array[FileStatus] = hdfs.listStatus(new Path(path))
    val arrPath: Array[Path] = FileUtil.stat2Paths(fs)
    var arrBuffer:ArrayBuffer[String]=ArrayBuffer()
    for(eachPath<-arrPath){
      arrBuffer+=(FolderPath+eachPath.getName)
    }
    arrBuffer
  }



  override def setProperties(map: Map[String, Any]): Unit = {
    FolderPath = MapUtil.get(map,"FolderPath").asInstanceOf[String]
    tag = MapUtil.get(map,"tag").asInstanceOf[String]

  }



  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val FolderPath = new PropertyDescriptor().name("FolderPath").displayName("FolderPath").description("The path of the json folder").defaultValue("").required(true)
    descriptor = FolderPath :: descriptor
    val tag = new PropertyDescriptor().name("tag").displayName("tag").description("The tag you want to parse,If you want to open an array field,you have to write it like this:links_name(MasterField_ChildField)").defaultValue("").required(false)
    descriptor = tag :: descriptor


    descriptor
  }



  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/json/FolderJsonPath.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JsonGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
