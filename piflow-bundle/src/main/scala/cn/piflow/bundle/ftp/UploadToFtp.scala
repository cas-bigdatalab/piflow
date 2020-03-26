package cn.piflow.bundle.ftp

import java.io.{DataOutputStream, File, InputStream, OutputStream}
import java.util

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import sun.net.TelnetOutputStream
import sun.net.ftp.{FtpClient, FtpDirEntry}

import scala.reflect.io.Directory

class UploadToFtp extends ConfigurableStop {
  val authorEmail: String = "xiaoxiao@cnic.cn"
  val description: String = "Upload file to ftp server"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url_str: String = _
  var port: Int = _
  var username: String = _
  var password: String = _
  var ftpFile: String = _
  var localPath: String = _
  var ftpClient: FtpClient = null

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    ftpClient = connectFTP(url_str, port, username, password)
    var filesList: util.ArrayList[String] = getFiles(localPath)
    for (i <- 0 until filesList.size()) {
      var file: File = new File(filesList.get(i))
      println(file.getParent + ":" + filesList.get(i) + ":" + file.getName)
      upload(filesList.get(i), file.getParent, file.getName)
    }
  }

  import sun.net.ftp.FtpProtocolException
  import java.io.IOException
  import java.net.InetSocketAddress

  def connectFTP(url: String, port: Int, username: String, password: String): FtpClient = { //创建ftp
    var ftp: FtpClient = null
    try { //创建地址
      val addr = new InetSocketAddress(url, port)
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

  def getFiles(localPath: String): util.ArrayList[String] = {
    var fileList: Array[File] = null
    var fileStrList = new util.ArrayList[String]()
    var path = new File(localPath)
    fileList = path.listFiles()
    println(fileList.length)
    for (i <- 0 until fileList.length) {
      if (fileList(i).isFile) {
        fileStrList.add(fileList(i).getParent + "/" + fileList(i).getName)
      } else if (fileList(i).isDirectory) {
        getFiles(fileList(i).getPath)
      }
    }

    return fileStrList
  }

  import sun.net.TelnetOutputStream
  import java.io.FileInputStream
  import java.io.FileNotFoundException
  import java.io.IOException

  /**
    * 上传文件到FTP
    *
    * @param sourcePath
    * @param filePath 要保存在FTP上的路径（文件夹）
    * @param fileName 文件名（test001.jpg）
    * @return 文件是否上传成功
    * @throws Exception
    */
  def upload(sourcePath: String, filePath: String, fileName: String): Boolean = {
    var to: TelnetOutputStream = null
    var fi: FileInputStream = null
    var f: File = new File(ftpFile)
    var ftpFilePath: String = f.getPath
    if (!(ftpClient.getWorkingDirectory.equals(ftpFilePath + filePath))) {
      println(ftpClient.getWorkingDirectory)
      ftpClient.changeDirectory(ftpFile)
      ftpClient.makeDirectory(filePath.replace("/", ""))
    }
    ftpClient.changeDirectory(ftpFilePath + filePath)
    ftpClient.setBinaryType()
    var file: File = new File(sourcePath)
    try {
      if (file != null) {
        fi = new FileInputStream(file)
        to = ftpClient.putFileStream(fileName, true).asInstanceOf[TelnetOutputStream]
        val bytes = new Array[Byte](1024)
        var byteRead = 0
        while (((byteRead = fi.read(bytes)) != -1) && (byteRead != -1)) {
          to.write(bytes, 0, byteRead)
        }
      }
      true
    } catch {
      case e1: FileNotFoundException =>
        false
      case e2: IOException =>
        false
      case e: Exception =>
        false
    } finally {
      if (fi != null) try
        fi.close()
      catch {
        case e: IOException =>
          e.printStackTrace()
      }
      if (to != null) try {
        to.flush()
        to.close()
      } catch {
        case e: IOException =>
          e.printStackTrace()
      }
    }
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map: Map[String, Any]): Unit = {
    url_str = MapUtil.get(map, key = "url_str").asInstanceOf[String]
    port = Integer.parseInt(MapUtil.get(map, key = "port").toString)
    username = MapUtil.get(map, key = "username").asInstanceOf[String]
    password = MapUtil.get(map, key = "password").asInstanceOf[String]
    ftpFile = MapUtil.get(map, key = "ftpFile").asInstanceOf[String]
    localPath = MapUtil.get(map, key = "localPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    val url_str = new PropertyDescriptor()
      .name("url_str")
      .displayName("URL")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = url_str :: descriptor

    val port = new PropertyDescriptor()
      .name("port")
      .displayName("Port")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = port :: descriptor

    val username = new PropertyDescriptor()
      .name("username")
      .displayName("User_Name")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = username :: descriptor

    val password = new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = password :: descriptor

    val ftpFile = new PropertyDescriptor()
      .name("ftpFile")
      .displayName("FTP_File")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = ftpFile :: descriptor

    val localPath = new PropertyDescriptor()
      .name("localPath")
      .displayName("Local_Path")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = localPath :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ftp/UpLoadToFtp.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.FtpGroup)
  }
}
