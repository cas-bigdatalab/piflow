package cn.piflow.bundle.ftp

import java.io.{ByteArrayOutputStream, File, InputStream}
import java.net.{HttpURLConnection, URL}
import java.util

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import sun.net.ftp.{FtpClient, FtpDirEntry}

import scala.reflect.io.Directory

class LoadFromFtp extends ConfigurableStop{
  val authorEmail: String = "xiaoxiao@cnic.cn"
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
    for(i<-0 until arrayList.size()){
      download(localPath,ftpFile+arrayList.get(i),arrayList.get(i))
    }
  }

  import sun.net.ftp.FtpProtocolException
  import java.io.IOException
  import java.net.InetSocketAddress
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

  import sun.net.ftp.FtpProtocolException
  import java.io.FileOutputStream
  import java.io.IOException

  def download(localPath: String, ftpFile: String,fileName:String): Unit = {
    var is:InputStream = null
    var fos:FileOutputStream = null
    try { // 获取ftp上的文件
      is = ftpClient.getFileStream(ftpFile)
      val savePath = new File(localPath)
      if(!savePath.exists()){
        savePath.mkdir()
      }
      var file=new File(savePath+"/"+fileName)
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

  import java.io.IOException
  import java.util.ArrayList
  def getFileList(path:String):ArrayList[String]={
    val fileLists = new ArrayList[String]
    // 获得指定目录下所有文件名
    var ftpFiles:util.Iterator[FtpDirEntry] = null
    try
      ftpFiles = ftpClient.listFiles(path)
    catch {
      case e: IOException =>
        e.printStackTrace()
    }
    while (ftpFiles.hasNext) {
      var file:FtpDirEntry=ftpFiles.next()
      if (file.getType.name()=="FILE") {
        System.out.println("文件夹下面的文件=====" + file.getName)
        fileLists.add(file.getName)
      }
      else if (file.isInstanceOf[Directory]) {
        System.out.println("文件夹名称为=====" + file.getName)
        val childLists = getFileList(path + file.getName + "/")
        for (i<-0 to childLists.size()) {
          fileLists.add(childLists.get(i))
        }
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
    val url_str = new PropertyDescriptor().name("url_str").displayName("URL").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").defaultValue("").required(true)
    val username = new PropertyDescriptor().name("username").displayName("USER_NAME").defaultValue("").required(true)
    val password = new PropertyDescriptor().name("password").displayName("PASSWORD").defaultValue("").required(true)
    val ftpFile = new PropertyDescriptor().name("ftpFile").displayName("FTP_File").defaultValue("").required(true)
    val localPath = new PropertyDescriptor().name("localPath").displayName("Local_Path").defaultValue("").required(true)
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
    List(StopGroup.FtpGroup.toString)
  }


}
