package cn.piflow.bundle.hdfs

import java.io._
import java.util.zip.GZIPInputStream

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.apache.tools.tar.{TarEntry, TarInputStream}

import scala.collection.mutable.ArrayBuffer

class UnzipFilesOnHDFS extends ConfigurableStop {
  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "Unzip files on HDFS"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var isCustomize:String=_
  var hdfsUrl:String=_
  var filePath:String=_
  var savePath:String=_

  var session: SparkSession = null
  var arr:ArrayBuffer[Row]=ArrayBuffer()


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    session = pec.get[SparkSession]()


    if(isCustomize.equals("true")){

      unzipFile(hdfsUrl+filePath,savePath)

    }else if (isCustomize .equals("false")){

      val inDf: DataFrame = in.read()
      inDf.collect().foreach(row => {
        filePath = row.get(0).asInstanceOf[String]
        unzipFile(filePath,savePath)

      })

    }

    val rdd: RDD[Row] = session.sparkContext.makeRDD(arr.toList)
    val fields: Array[StructField] =Array(StructField("savePath",StringType,nullable = true))
    val schema: StructType = StructType(fields)
    val df: DataFrame = session.createDataFrame(rdd,schema)

    println("##################################################################################################")
    //    println(df.count())
    df.show(20)
    println("##################################################################################################")

    out.write(df)

  }


  def whatType(p:String): String = {
    var typeStr:String=""
    val pathNames: Array[String] = p.split("\\.")
    val lastStr: String = pathNames.last
    if(lastStr.equals("gz")){
      val penultStr: String = pathNames(pathNames.length-2)
      if(penultStr.equals("tar")){
        typeStr="tar.gz"
      }else {
        typeStr="gz"
      }
  }else{
      throw new RuntimeException("File type fill in error, or do not support this type.")
    }
    typeStr
  }


  def getFs(fileHdfsPath: String): FileSystem = {
    var configuration: Configuration = new Configuration()
    var fs: FileSystem =null
    if (isCustomize.equals("false")) {
      val pathARR: Array[String] = fileHdfsPath.split("\\/")
      hdfsUrl = ""
      for (x <- (0 until 3)) {
        hdfsUrl += (pathARR(x) + "/")
      }
    }
    configuration.set("fs.defaultFS", hdfsUrl)
    fs = FileSystem.get(configuration)
    fs
  }




  def unzipFile(fileHdfsPath: String, saveHdfsPath: String)= {
    var eachSavePath : String=""

    var unType: String = whatType(fileHdfsPath)
    var fileName: String = fileHdfsPath.split("\\/").last
    var fs: FileSystem= getFs(fileHdfsPath)

    var sp:String=""
    if(saveHdfsPath.length < 1){
      sp=fileHdfsPath.replace(fileName,"")
    }else{
      sp = hdfsUrl + saveHdfsPath
    }

    val fdis: FSDataInputStream = fs.open(new Path(fileHdfsPath))


    if(unType.equals("gz")){
      val gzip: GZIPInputStream = new GZIPInputStream(fdis)
      var n = -1
      val buf=new Array[Byte](10*1024*1024)

      eachSavePath = sp +fileName.replace(".gz","")
      arr += Row.fromSeq(Array(eachSavePath))
      val path = new Path(eachSavePath)
      val fdos = fs.create(path)
      while((n=gzip.read(buf)) != -1 && n != -1){
        fdos.write(buf,0,n)
        fdos.flush()
      }
      fdos.close()
      gzip.close()
      fdis.close()
    }else if(unType.equals("tar.gz")){

      try {
        val gzip = new GZIPInputStream(new BufferedInputStream(fdis))
        val tarIn = new TarInputStream(gzip, 1024 * 2)

//        fs.create(new Path(sp)).close()

        var entry: TarEntry = null

        while ((entry = tarIn.getNextEntry) != null  && entry !=null) {

          if (entry.isDirectory()) {
            val outPath = sp + "/" + entry.getName
            fs.create(new Path(outPath)).close()

          } else {
            val outPath = sp + "/" + entry.getName

            arr += Row.fromSeq(Array(outPath))
            val fos: FSDataOutputStream = fs.create(new Path(outPath))

            var lenth = 0
            val buff = new Array[Byte](1024)
            while ((lenth = tarIn.read(buff)) != -1 && (lenth != -1)) {
              fos.write(buff, 0, lenth)
            }
            fos.close()
          }
        }
      }catch {
        case  e: IOException =>
          e.printStackTrace()
      }

    }
  }


  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    isCustomize=MapUtil.get(map,key="isCustomize").asInstanceOf[String]
    filePath=MapUtil.get(map,key="filePath").asInstanceOf[String]
    hdfsUrl=MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    savePath=MapUtil.get(map,key="savePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val filePath = new PropertyDescriptor().name("filePath").displayName("filePath").description("file path,such as /a/a.gz").defaultValue("").required(false)
    val hdfsUrl = new PropertyDescriptor().name("hdfsUrl").displayName("hdfsUrl").description("the url of HDFS,such as hdfs://10.0.86.89:9000").defaultValue("").required(false)
    val savePath = new PropertyDescriptor().name("savePath").displayName("savePath").description("unzip dir or file path, such as /b/ or /b/b.gz").defaultValue("").required(true)
    val isCustomize = new PropertyDescriptor().name("isCustomize").displayName("isCustomize").description("Whether to customize the compressed file path, if true, " +
                                                                                                          "you must specify the path where the compressed file is located . " +
                                                                                                          "If it is false, it will automatically find the file path data from the upstream port ")
                                                                                                          .defaultValue("").required(false)
    descriptor = isCustomize :: descriptor
    descriptor = filePath :: descriptor
    descriptor = hdfsUrl :: descriptor
    descriptor = savePath :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("hdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup.toString)
  }
}
