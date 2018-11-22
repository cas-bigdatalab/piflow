package cn.piflow.bundle.ftp

import java.io.{File, InputStream}
import java.util
import java.util.ArrayList

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import sun.net.ftp.{FtpClient, FtpDirEntry}

import scala.reflect.io.Directory

class NewLoadFromFtp extends ConfigurableStop{
  val authorEmail: String = "yg@cnic.cn"
  val description: String = "Load file from ftp server."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)

  var url_str:String =_
  var port:Int=_
  var username:String=_
  var password:String=_
  var ftpFile:String=_
  var localPath:String=_

  var ftpClient:FtpClient=null
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {


    ftpClient=connectFTP(url_str,port,username,password)
    var arrayList:util.ArrayList[String]=getFileList(ftpFile)
    //println(arrayList.size()+"================================size")

    for(i<-0 until arrayList.size()){
      println("++++++++++++++++++++++++++++++++++++++++++++++++++++++filename")

      val aa  = arrayList.get(i).split("yg00  00gyxx00")
      println(aa(0))
      println(aa(1))

      //localPath    ftpFile   filename
      download(localPath,aa(0),aa(1))
    }
  }

  import java.io.IOException
  import java.net.InetSocketAddress

  import sun.net.ftp.FtpProtocolException
  def connectFTP(url: String, port: Int, username: String, password: String): FtpClient = { //创建ftp
    var ftp:FtpClient = null
    try { //创建地址
      val addr = new InetSocketAddress(url,port)
      //连接
      ftp = FtpClient.create
      ftp.connect(addr)
      //登陆
      ftp.login(username, password.toCharArray)
      ftp.setBinaryType
    } catch {
      case e: FtpProtocolException =>
        e.printStackTrace()
      case e: IOException =>
        e.printStackTrace()
    }
    ftp
  }

  import java.io.{FileOutputStream, IOException}

  import sun.net.ftp.FtpProtocolException

  def download(localPath: String, ftpFile: String,fileName:String): Unit = {
    var is:InputStream = null
    var fos:FileOutputStream = null
    try { // 获取ftp上的文件
      is = ftpClient.getFileStream(ftpFile+fileName)
      val savePath = new File(localPath+ftpFile)
      println(savePath+"88888888888888888888888888888888888888888888888888")
      if(!savePath.exists()){
        savePath.mkdirs()
      }
      var file=new File(savePath+"/"+fileName)
     // println(file+"****************************************")
      if(file!=null || !file.exists()){
        file.createNewFile()
      }
      val bytes = new Array[Byte](1024)
      var byteRead = 0
      fos = new FileOutputStream(file)
      while ( ((byteRead=is.read(bytes)) != -1) && (byteRead != -1)) {
        fos.write(bytes, 0, byteRead)
      }
      System.out.println("download success!!")
    } catch {
      case e: FtpProtocolException =>
        e.printStackTrace()
      case e: IOException =>
        e.printStackTrace()
    } finally try {
      if (fos != null) fos.close()
      if (is != null) is.close
    } catch {
      case e: IOException =>
        e.printStackTrace()
    }
  }

  var fileLists = new ArrayList[String]
  import java.io.IOException
  import java.util.ArrayList
  def getFileList(path:String):ArrayList[String]={

    // 获得指定目录下所有文件名
    var ftpFiles:util.Iterator[FtpDirEntry] = null
    try {
      ftpFiles = ftpClient.listFiles(path)
    }
    catch {
      case e: IOException =>
        e.printStackTrace()
    }
    while (ftpFiles.hasNext) {
      var file:FtpDirEntry=ftpFiles.next()
      if (file.getType.name()=="FILE") {

//        println("文件夹下面的文件====="+path +file.getName)

//       println(file.getName)
        fileLists.add(path+ "yg00  00gyxx00"+file.getName)

      }
      else  {

//        println("文件夹名称为=====" + file.getName)
        getFileList(path + file.getName + "/")



      }
    }
    return fileLists
  }



  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    url_str=MapUtil.get(map,key="url_str").asInstanceOf[String]
    port=Integer.parseInt(MapUtil.get(map,key="port").toString)
    username=MapUtil.get(map,key="username").asInstanceOf[String]
    password=MapUtil.get(map,key="password").asInstanceOf[String]
    ftpFile=MapUtil.get(map,key="ftpFile").asInstanceOf[String]
    localPath=MapUtil.get(map,key="localPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url_str = new PropertyDescriptor().name("url_str").displayName("url_str").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("port").defaultValue("").required(true)
    val username = new PropertyDescriptor().name("username").displayName("username").defaultValue("").required(true)
    val password = new PropertyDescriptor().name("password").displayName("password").defaultValue("").required(true)
    val ftpFile = new PropertyDescriptor().name("ftpFile").displayName("ftpFile").defaultValue("").required(true)
    val localPath = new PropertyDescriptor().name("localPath").displayName("localPath").defaultValue("").required(true)
    descriptor = url_str :: descriptor
    descriptor = port :: descriptor
    descriptor = username :: descriptor
    descriptor = password :: descriptor
    descriptor = ftpFile :: descriptor
    descriptor = localPath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("ftp.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.FtpGroup.toString)
  }


}
