package cn.piflow.bundle.ftp

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.commons.net.ftp.{FTP, FTPClient, FTPClientConfig, FTPFile}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataOutputStream, FileSystem, Path}

class LoadFromFtpToHDFS extends ConfigurableStop {
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Download files or folders to save to HDFS"
  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)

  var url_str:String =_
  var port:String=_
  var username:String=_
  var password:String=_
  var ftpFile:String=_
  var HDFSUrl:String=_
  var HDFSPath:String=_
  var isFile:String=_

  var fs: FileSystem=null
  var con: FTPClientConfig =null

  def downFile(ftp: FTPClient,ftpFilePath:String,HDFSSavePath:String): Unit = {
    val changeFlag: Boolean = ftp.changeWorkingDirectory(ftpFilePath)
    if(changeFlag){
      println("change dir successful   "+ftpFilePath)

      val files: Array[FTPFile] = ftp.listFiles()

      for(x <- files ) {
        if (x.isFile) {
          ftp.changeWorkingDirectory(ftpFilePath)
          println("down start  ^^^  "+x.getName)
          val hdfsPath: Path = new Path(HDFSSavePath + x.getName)
          if(! fs.exists(hdfsPath)){
            var fdos: FSDataOutputStream = fs.create(hdfsPath)

            val b = ftp.retrieveFile(new String(x.getName.getBytes("GBK"),"ISO-8859-1"), fdos)
            if(b){
              println("down successful   " + x.getName)
            }else{
              throw new Exception("down error")
            }
            fdos.close()
          }
        } else {
          downFile(ftp,ftpFilePath+x.getName+"/",HDFSSavePath+x.getName+"/")
        }
      }
    }else{
      throw new Exception("File path error")
    }

  }


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val configuration: Configuration = new Configuration()
    configuration.set("fs.defaultFS", HDFSUrl)
    fs = FileSystem.get(configuration)

    val ftp:FTPClient = openFtpClient()

    if(isFile.equals("true")){
      val pathArr: Array[String] = ftpFile.split("/")
      var dirPath:String=""
      for(x <- (0 until pathArr.length-1)){
        dirPath += (pathArr(x)+"/")
      }
      val boolChange: Boolean = ftp.changeWorkingDirectory(dirPath)

      if(boolChange){
        println("change dir successful   "+dirPath)
        var fdos: FSDataOutputStream = fs.create(new Path(HDFSPath+pathArr.last))
        println("down start   "+pathArr.last)
        val boolDownSeccess: Boolean = ftp.retrieveFile(new String(pathArr.last.getBytes("GBK"),"ISO-8859-1"), fdos)
        if(boolDownSeccess){
          println("down successful   "+pathArr.last)
        }else{
          throw new Exception("down error")
        }
        fdos.flush()
        fdos.close()
      }else{
        throw new Exception("File path error")
      }

    }else{
      downFile(ftp,ftpFile,HDFSPath)
    }
  }

  def openFtpClient(): FTPClient = {
    val ftp = new FTPClient

    try{
      if(port.length > 0 ){
        ftp.connect(url_str,port.toInt)
      }else{
        ftp.connect(url_str)
      }
    }catch {
      case e:Exception => throw new Exception("Failed to connect FTP server")
    }

    try{
      if(username.length > 0 && password.length > 0){
        ftp.login(username,password)
      }else{
        ftp.login("anonymous", "121@hotmail.com")
      }
    }catch {
      case e:Exception => throw new Exception("Failed to log on to FTP server")
    }

    ftp.setControlEncoding("GBK")
    con = new FTPClientConfig(FTPClientConfig.SYST_NT)
    con.setServerLanguageCode("zh")
    ftp.setFileType(FTP.BINARY_FILE_TYPE)
    ftp.setDataTimeout(600000)
    ftp.setConnectTimeout(600000)
    ftp.enterLocalPassiveMode()//被动模式
    ftp.setControlEncoding("UTF-8")
    ftp
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    url_str=MapUtil.get(map,key="url_str").asInstanceOf[String]
    port=MapUtil.get(map,key="port").asInstanceOf[String]
    username=MapUtil.get(map,key="username").asInstanceOf[String]
    password=MapUtil.get(map,key="password").asInstanceOf[String]
    ftpFile=MapUtil.get(map,key="ftpFile").asInstanceOf[String]
    HDFSUrl=MapUtil.get(map,key="HDFSUrl").asInstanceOf[String]
    HDFSPath=MapUtil.get(map,key="HDFSPath").asInstanceOf[String]
    isFile=MapUtil.get(map,key="isFile").asInstanceOf[String]
  }


  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url_str = new PropertyDescriptor().name("url_str").displayName("URL").defaultValue("IP of FTP server, such as 128.136.0.1 or ftp.ei.addfc.gak").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").defaultValue("Port of FTP server").required(false)
    val username = new PropertyDescriptor().name("username").displayName("USER_NAME").defaultValue("").required(false)
    val password = new PropertyDescriptor().name("password").displayName("PASSWORD").defaultValue("").required(false)
    val ftpFile = new PropertyDescriptor().name("ftpFile").displayName("FTP_File").defaultValue("The path of the file to the FTP server, such as /test/Ab/ or /test/Ab/test.txt").required(true)
    val HDFSUrl = new PropertyDescriptor().name("HDFSUrl").displayName("HDFSUrl").defaultValue("The URL of the HDFS file system, such as hdfs://10.0.88.70:9000").required(true)
    val HDFSPath = new PropertyDescriptor().name("HDFSPath").displayName("HDFSPath").defaultValue("The save path of the HDFS file system, such as /test/Ab/").required(true)
    val isFile = new PropertyDescriptor().name("isFile").displayName("isFile").defaultValue("Whether the path is a file or not, if true is filled in, only a single file specified by the path is downloaded. If false is filled in, all files under the folder are downloaded recursively.").required(true)
    descriptor = isFile :: descriptor
    descriptor = url_str :: descriptor
    descriptor = port :: descriptor
    descriptor = username :: descriptor
    descriptor = password :: descriptor
    descriptor = ftpFile :: descriptor
    descriptor = HDFSUrl :: descriptor
    descriptor = HDFSPath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("ftp.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.FtpGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }


}
