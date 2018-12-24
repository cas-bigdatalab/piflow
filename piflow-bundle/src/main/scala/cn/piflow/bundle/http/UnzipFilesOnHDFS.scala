package cn.piflow.bundle.http

import java.util.zip.GZIPInputStream

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

import scala.collection.mutable.ArrayBuffer

class UnzipFilesOnHDFS extends ConfigurableStop {
  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "Unzip files on HDFS"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var isCustomize:String=_
  var filePath:String=_
  var fileType:String=_
  var unzipPath:String=_


  var session: SparkSession = null

  def unzipFile(hdfsFilePath: String, zipFileType: String, unzipHdfsPath: String):String = {
    var zft: String = ""
    if(zipFileType.length < 1){
      zft = hdfsFilePath.split("\\.").last
    }else{
      zft = zipFileType
    }

    val configuration: Configuration = new Configuration()
    val pathARR: Array[String] = hdfsFilePath.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){

      hdfsUrl+=(pathARR(x) +"/")
    }
    configuration.set("fs.defaultFS",hdfsUrl)

    var uhp : String=""
    if(unzipHdfsPath.length < 1){
      for (x <- (0 until pathARR.length-1)){
        uhp+=(pathARR(x) +"/")
      }
    }else{
      uhp=unzipHdfsPath
    }

    val fs = FileSystem.get(configuration)
    val fdis: FSDataInputStream = fs.open(new Path(hdfsFilePath))
    val filePathArr: Array[String] = hdfsFilePath.split("/")
    var fileName: String = filePathArr.last
    if(fileName.length == 0){
      fileName = filePathArr(filePathArr.size-2)
    }

    var savePath:String=""

    if(zft.equals("gz")){
      val gzip: GZIPInputStream = new GZIPInputStream(fdis)
      var n = -1
      val buf=new Array[Byte](10*1024*1024)
      savePath = uhp +fileName.replace(".gz","")
      val path = new Path(savePath)
      val fdos = fs.create(path)
      while((n=gzip.read(buf)) != -1 && n != -1){
        fdos.write(buf,0,n)
        fdos.flush()
      }
      fdos.close()
      gzip.close()
      fdis.close()
    }else{
      throw new RuntimeException("File type fill in error, or do not support this type.")
    }

    savePath

  }

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    session = pec.get[SparkSession]()

    var savePath: String = ""
    var arr:ArrayBuffer[Row]=ArrayBuffer()


    if(isCustomize.equals("true")){
      println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

      savePath = unzipFile(filePath,fileType,unzipPath)


      println("savepath  :  "+savePath)

      arr += Row.fromSeq(Array(savePath))

    }else if (isCustomize.equals("false")){

      val inDf: DataFrame = in.read()
      inDf.collect().foreach(row => {

        filePath = row.get(0).asInstanceOf[String]
        savePath = unzipFile(filePath,"","")
        arr += Row.fromSeq(Array(savePath))
        savePath = ""

      })

    }

    val rdd: RDD[Row] = session.sparkContext.makeRDD(arr.toList)
    val fields: Array[StructField] =Array(StructField("unzipPath",StringType,nullable = true))
    val schema: StructType = StructType(fields)
    val df: DataFrame = session.createDataFrame(rdd,schema)

    println("##################################################################################################")
//    println(df.count())
    df.show(20)
    println("##################################################################################################")

    out.write(df)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    isCustomize=MapUtil.get(map,key="isCustomize").asInstanceOf[String]
    filePath=MapUtil.get(map,key="filePath").asInstanceOf[String]
    fileType=MapUtil.get(map,key="fileType").asInstanceOf[String]
    unzipPath=MapUtil.get(map,key="unzipPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val filePath = new PropertyDescriptor().name("filePath").displayName("filePath").description("file path,such as hdfs://10.0.86.89:9000/a/a.gz").defaultValue("").required(false)
    val fileType = new PropertyDescriptor().name("fileType").displayName("fileType").description("file type,such as gz").defaultValue("").required(false)
    val unzipPath = new PropertyDescriptor().name("unzipPath").displayName("unzipPath").description("unzip path, such as hdfs://10.0.86.89:9000/b/").defaultValue("").required(true)
    val isCustomize = new PropertyDescriptor().name("isCustomize").displayName("isCustomize").description("Whether to customize the compressed file path, if true, " +
                                                                                                          "you must specify the path where the compressed file is located and the saved path after decompression. " +
                                                                                                          "If it is fals, it will automatically find the file path data from the upstream port and " +
                                                                                                          "save it to the original folder after decompression.")
                                                                                                          .defaultValue("").required(false)
    descriptor = isCustomize :: descriptor
    descriptor = filePath :: descriptor
    descriptor = fileType :: descriptor
    descriptor = unzipPath :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("http.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.HttpGroup.toString)
  }

}
