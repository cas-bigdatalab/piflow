package cn.piflow.bundle.ftp

import java.io._
import java.net.URL
import java.util.ArrayList

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession
import org.jsoup.Jsoup
import org.jsoup.select.Elements
import sun.net.ftp.FtpProtocolException


class LoadFromFtpUrl extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Load file from ftp url."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)

  var url_str:String =_
  var url_type:String =_
  var localPath:String =_

  var list = List("")


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    import spark.sqlContext.implicits._


    var filePath:String = null


    if (url_type == "file"){
      val aa  = url_str.split("/")
      val fileName = aa(aa.size-1)
      println(fileName)
      filePath = localPath+"/"+fileName
      list = filePath::list
      downFileFromFtpUrl(url_str,localPath,fileName)

    } else {

      var arrayList:ArrayList[String]=getFilePathList(url_str)

      for (i <- 0 until arrayList.size()) {
        //println(arrayList.get(i))
        val aa = arrayList.get(i).split("--1234567890987654321--")
        val bb = arrayList.get(i).replace(s"$url_str", "/").split("--1234567890987654321--")
        filePath = localPath + bb(0) + aa(1)
        list = filePath :: list
        downFileFromFtpUrl(aa(0) + aa(1), localPath + bb(0), aa(1))
      }
    }

    val outDF = sc.parallelize(list).toDF("filePath")
    println(outDF.count())
    outDF.show()
    out.write(outDF)

  }


  def downFileFromFtpUrl(url: String,saveDir:String,fileName:String): Unit ={
    var bos:BufferedOutputStream = null
    var is :InputStream =null
    try {
      val buff = new Array[Byte](1024)
      is = new URL(url).openStream()
      val file = new File(saveDir, fileName)
      file.getParentFile.mkdirs
      bos = new BufferedOutputStream(new FileOutputStream(file))
      var count = 0
      while ((count = is.read(buff)) != -1 && (count != -1)) {
        bos.write(buff, 0, count)
      }
    }
    catch  {
      case e: FtpProtocolException =>
        e.printStackTrace()
      case e: IOException =>
        e.printStackTrace()
    } finally try {
      if (bos != null) bos.close()
      if (is != null) is.close
    } catch {
      case e: IOException =>
        e.printStackTrace()
    }

  }


  // 获取ftp上的文件 path
  var filePathList = new ArrayList[String]
  def getFilePathList(url:String):ArrayList[String] ={


    val doc = Jsoup.connect(url).timeout(100000000).get()
    val selectStr = "body>pre>a"
    val elements: Elements = doc.select("body>pre>a")

    for (i <- 0 until elements.size()) {
      val fileName = elements.get(i).text()

      // Parent Directory
      if (fileName.contains("Parent Directory")) {
        println(fileName + "---------------" + "父目录")
      }
      // Directory
      else if (fileName.contains("/")) {
        //println(fileName+"********************************"+"文件夹")
        var url0 = ""
        if (url.endsWith("/")) {
          url0 = url + fileName
        } else {
          url0 = url + "/" + fileName
        }
        //println(url0)
        //recursive query
        getFilePathList(url0)
      } else {
        filePathList.add(url + "--1234567890987654321--" + fileName)
        //println(url+fileName)
      }
    }

    return filePathList
  }



  def setProperties(map: Map[String, Any]): Unit = {
    url_str=MapUtil.get(map,key="url_str").asInstanceOf[String]
    url_type=MapUtil.get(map,key="url_type").asInstanceOf[String]
    localPath=MapUtil.get(map,key="localPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url_str = new PropertyDescriptor().name("url_str").displayName("URL").defaultValue("").required(true)
    val localPath = new PropertyDescriptor().name("localPath").displayName("Local_Path").defaultValue("").required(true)
    val  url_type= new PropertyDescriptor().name("url_type").displayName("url_type").defaultValue("").required(false)


    descriptor = url_str :: descriptor
    descriptor = url_type :: descriptor
    descriptor = localPath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("ftp.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.FtpGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}