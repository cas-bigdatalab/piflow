package cn.piflow.bundle.ftp


import java.io._
import java.net.URL
import java.text.SimpleDateFormat
import java.util.{ArrayList, Date}

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
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var http_URl:String =_  //url 地址
  var url_type:String =_   // url 指向文件 类型，文件 or 文件夹
  var localPath:String =_   // 保存的本地路径
  var downType:String=_
  var fileName:String=_

  var list = List("")

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    import spark.sqlContext.implicits._

    var fileLocalPath:String = null
    // 具体的文件路径  直接下载
    if (url_type == "file"){
      println("************************************************    -----------file ")
     // val aa  = url_str.split("/")
      // 文件名字
      //val fileName = aa(aa.size-1)
      println(fileName)
      //文件 路径保存到 list
      fileLocalPath = localPath+"/"+fileName
      list = fileLocalPath::list
      // 下载 文件
      downFileFromFtpUrl(http_URl,localPath,fileName)
    } else {
      var arrayList:ArrayList[String]=getFilePathList(http_URl)
      // 遍历 文件路径 所在的集合
      for (i <- 0 until arrayList.size()) {
        // https://ftp.ncbi.nih.gov/genbank/docs/--1234567890987654321--Current_version_is_10.7--1234567890987654321--20180423
        val array = arrayList.get(i)

        if(downType.equals("all")){

          val arrayString = array.split("--1234567890987654321--")

          val fileUrlDir = array.replace(s"$http_URl", "/").split("--1234567890987654321--")(0)
          // 单个文件url 指向的 路径
          val urlPath = arrayString(0)+arrayString(1)
          // 下载 保存 文件夹的目录
          val savePath = localPath+fileUrlDir
          // 文件名字
          val fileName = arrayString(1)

          fileLocalPath = savePath+fileName
          println(urlPath)
          println(savePath)
          println(fileName)

          list = fileLocalPath :: list

          downFileFromFtpUrl(urlPath, savePath, fileName)

        } else {
          println("##################################")
          // 增量下载  ,下载当天数据
          var now = new Date()
          var dateFormeat = new SimpleDateFormat("yyyy-MM-dd")
          val todayDate = dateFormeat.format(now)
          println(todayDate)

          if(array.endsWith(todayDate)){
            println("##################################_____-------------------------------")
            val arrayString = array.split("--1234567890987654321--")

            val fileUrlDir = array.replace(s"$http_URl", "/").split("--1234567890987654321--")(0)
            // 单个文件url 指向的 路径
            val urlPath = arrayString(0)+arrayString(1)
            // 下载 保存 文件夹的目录
            val savePath = localPath+fileUrlDir
            // 文件名字
            val fileName = arrayString(1)

            fileLocalPath = savePath+fileName
            println(urlPath)
            println(savePath)
            println(fileName)

            list = fileLocalPath :: list

            downFileFromFtpUrl(urlPath, savePath, fileName)
          }
        }
      }
    }
    //  保存的本地文件 路径 ，加载到 df 里面  ，字段名字为 filepath
    val outDF = sc.parallelize(list).toDF("filePath")
    println(outDF.count())
    outDF.show()
    out.write(outDF)

  }


  //  下载文件从 url 上
  //   URL网址   保存路径   保存文件名字
  def downFileFromFtpUrl(url: String,saveDir:String,fileName:String): Unit ={
    var bos:BufferedOutputStream = null
    var is :InputStream =null
    try {

      val buff = new Array[Byte](1024)
      is = new URL(url).openStream()


//      val configuration: Configuration = new Configuration()
//      val fs = FileSystem.get(configuration)
//      val out: FSDataOutputStream = fs.create(new Path(saveDir))

      val file = new File(saveDir, fileName)
      // 级联创建文件夹  以及文件
      file.getParentFile.mkdirs
       // 输出流的路径
      bos = new BufferedOutputStream(new FileOutputStream(file))

      var count = 0
      // 写文件
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


  // 获取ftp上的文件 的路径
  var filePathList = new ArrayList[String]
  def getFilePathList(url:String):ArrayList[String] ={

    val doc = Jsoup.connect(url).timeout(100000000).get()
    //  获取 url 界面   文件名字  日期   大小
    //  Name                    Last modified      Size  Parent Directory                             -
    //  build_gbff_cu.pl        2003-04-25 17:23   21K

    val elements: Elements = doc.select("html >body >pre")
    println(elements.first().text())

    // 按行 分割 elements 为单个字符串
    val fileString = elements.first().text().split("\\n")

    for (i <- 0 until fileString.size) {

      // Parent Directory
      if(fileString(i).contains("Parent Directory")) {
        println(fileString(i) + "---------------" + "父目录")
      } else {
        // 分割单个字符串
        // build_gbff_cu.pl        2003-04-25 17:23   21K
        val aa = fileString(i).split("\\s+")
        // 获取文件 名字
        val fileName = aa(0)
        // 获取文件 日期
        val fileDate = aa(1)
        println(fileDate)

        // Directory
        if (fileName.contains("/")) {
          println(fileName+"********************************"+"文件夹")
          var url0 = ""
          if (url.endsWith("/")) {
            url0 = url + fileName
          } else {
            url0 = url + "/" + fileName
          }
          println(url0)
          //recursive query
          getFilePathList(url0)
        } else {
          // 保存 url文件路径到 集合中
          filePathList.add(url + "--1234567890987654321--" + fileName+"--1234567890987654321--"+fileDate)
          //println(url+fileName)
        }

      }
      // Directory
    }
    return filePathList
  }



  def setProperties(map: Map[String, Any]): Unit = {
    http_URl=MapUtil.get(map,key="http_URl").asInstanceOf[String]
    url_type=MapUtil.get(map,key="url_type").asInstanceOf[String]
    localPath=MapUtil.get(map,key="localPath").asInstanceOf[String]
    downType=MapUtil.get(map,key="downType").asInstanceOf[String]
    fileName=MapUtil.get(map,key="fileName").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val http_URl = new PropertyDescriptor().name("http_URl").displayName("http_URl").defaultValue("").required(true)
    val localPath = new PropertyDescriptor().name("localPath").displayName("Local_Path").defaultValue("").required(true)
    val  url_type= new PropertyDescriptor().name("url_type").displayName("url_type").defaultValue("").required(true)
    val  downType= new PropertyDescriptor().name("downType").displayName("downType").defaultValue("all,day").required(true)
    val  fileName= new PropertyDescriptor().name("fileName").displayName("fileName").defaultValue("fileName").required(false)


    descriptor = http_URl :: descriptor
    descriptor = url_type :: descriptor
    descriptor = localPath :: descriptor
    descriptor = downType :: descriptor
    descriptor = fileName :: descriptor
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