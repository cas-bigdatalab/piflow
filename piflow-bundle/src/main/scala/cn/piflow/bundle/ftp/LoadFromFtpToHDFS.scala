package cn.piflow.bundle.ftp

import java.text.NumberFormat
import java.util.regex.Pattern

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import com.enterprisedt.net.ftp._
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataOutputStream, FileSystem, Path}
import org.apache.log4j.Logger

import scala.collection.mutable.ArrayBuffer

class LoadFromFtpToHDFS extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Download files or folders to HDFS"
  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)

  var ftp_url:String =_
  var port:String=_
  var username:String=_
  var password:String=_
  var ftpFile:String=_
  var HDFSUrl:String=_
  var HDFSPath:String=_
  var isFile:String=_
  var filterByName : String = _

  var ftp:FileTransferClient = null
  var errorFile : ArrayBuffer[String]=ArrayBuffer()
  var filters: Array[String]=null
  var myException : Exception = null
  var boo : Boolean = true
  var fs: FileSystem=null
  var log: Logger =null


  def ftpConnect(): Unit = {
    var isConnect : Boolean = false
    var count : Int = 0
    while ( (! isConnect) && (count < 5) ){
      count += 1
      try{
        ftp.connect()
        isConnect = true
      }catch {
        case e : Exception => {
          isConnect = false
          log.warn("Retry the connection")
          Thread.sleep(1000*60*3)
        }
      }
    }
  }

  def openFtpClient(): Unit = {
    ftp = null

    ftp = new FileTransferClient
    ftp.setRemoteHost(ftp_url)
    if(port.size > 0){
      ftp.setRemotePort(port.toInt)
    }
    if(username.length > 0){
      ftp.setUserName(username)
      ftp.setPassword(password)
    }else{
      ftp.setUserName("anonymous")
      ftp.setPassword("anonymous")
    }
    ftp.setContentType(FTPTransferType.BINARY)
    ftp.getAdvancedFTPSettings.setConnectMode(FTPConnectMode.PASV)
    var isConnect : Boolean = true
    ftpConnect()
  }

  def copyFile(fileDir: String, fileNmae: String, HdfsPath: String) : Unit = {
    openFtpClient()
    try{
      var ftis: FileTransferInputStream = ftp.downloadStream(fileDir+fileNmae)
      var fileSize: Double = 0
      var whetherShowdownloadprogress : Boolean = true
      try {
        fileSize = ftp.getSize(fileDir + fileNmae).asInstanceOf[Double]
      }catch {
        case e : Exception => {
          whetherShowdownloadprogress = false
          log.warn("File size acquisition failed")
        }
      }
      val path: Path = new Path(HdfsPath + fileNmae)
      var hdfsFileLen: Long = -100
      if(fs.exists(path)){
        hdfsFileLen = fs.getContentSummary(path).getLength
      }
      if(hdfsFileLen != fileSize ){
        var fdos: FSDataOutputStream = fs.create(path)

        val bytes: Array[Byte] = new Array[Byte](1024*1024*10)
        var downSize:Double=0
        var n = -1
        while (((n = ftis.read(bytes)) != -1) && (n != -1)){
          fdos.write(bytes,0,n)
          fdos.flush()
          downSize += n
          if(whetherShowdownloadprogress){
            val percentageOfProgressStr: String = NumberFormat.getPercentInstance.format(downSize/fileSize)
            log.debug(fileDir+fileNmae+"  Download complete  "+percentageOfProgressStr)
          }
        }
        ftis.close()
        fdos.close()
        ftp.disconnect()
        boo = true
        log.debug("Download complete---"+fileDir+fileNmae)
      }
    }catch {
      case e : Exception => {
        boo = false
        myException = e
      }
    }
  }

  def getFtpList(ftpDir: String): Array[FTPFile]= {
    var fileArr: Array[FTPFile] = null
    try{
      fileArr = ftp.directoryList(ftpDir)
    }catch {
      case e :Exception => {
        myException = e
      }
    }
    fileArr
  }

  def downFileDir(ftpDir: String, HdfsDir: String): Unit = {
    openFtpClient()
    var fileArr: Array[FTPFile] = getFtpList(ftpDir)
    var countOfFileList:Int=0
    while (fileArr == null  &&  countOfFileList < 5){
      countOfFileList += 1
      if(fileArr == null){
        Thread.sleep(1000*60*3)
        openFtpClient()
        fileArr = getFtpList(ftpDir)
        log.warn("Retry the list of files---" +ftpDir )
      }
    }
    if(fileArr == null  && countOfFileList == 5){
      errorFile += ftpDir
    }else if(fileArr != null){
      log.debug("Getted list of files---"+ftpDir)
      try{
        ftp.disconnect()
      }catch {
        case e :Exception => log.warn("Failed to disconnect FTP server")
      }
      fileArr.foreach(eachFile => {
        val fileName: String = eachFile.getName
        if(eachFile.isDir && ! eachFile.isFile){
          downFileDir(ftpDir+fileName+"/",HdfsDir+fileName+"/")
        }else if(! eachFile.isDir && eachFile.isFile){
          var witherDown = true
          if(filters.size > 0){
            witherDown = false
            filters.foreach(each => {
              if(! witherDown){
                witherDown = Pattern.matches(each,fileName)
              }
            })
          }
          if(witherDown){
            log.debug("Start downloading---"+ftpDir+fileName)
            copyFile(ftpDir,fileName,HdfsDir)
            var count = 0
            while ((! boo) && (count < 5)){
              count += 1
              Thread.sleep(1000*60*3)
              copyFile(ftpDir,fileName,HdfsDir)
              log.warn("Try downloading files again---" + ftpDir+fileName)
            }
            if((! boo) && (count == 5)){
              errorFile += (ftpDir+fileName)
            }
          }
        }else{
          println(ftpDir+fileName+ "---Neither file nor folder")
          errorFile += (ftpDir+fileName)
        }
      })
    }
  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    log = Logger.getLogger(classOf[LoadFromFtpToHDFS])

    val configuration: Configuration = new Configuration()
    configuration.set("fs.defaultFS", HDFSUrl)
    fs = FileSystem.get(configuration)

    if(filterByName.length == 0){
      filterByName=".*"
    }
    filters = filterByName.split(";")

    if(isFile.equals("true") || isFile.equals("TRUE")){
      val fileNmae: String = ftpFile.split("/").last
      val fileDir = ftpFile.replace(fileNmae,"")
      copyFile(fileDir,fileNmae,HDFSPath)
    }else if(isFile.equals("false") || isFile.equals("FALSE")){
      downFileDir(ftpFile,HDFSPath)
    }else{
      throw new Exception("Please specify whether it is a file or directory.")
    }

    if(errorFile.size > 0){
      errorFile.foreach(x =>{
        log.warn("Download failed---"+x)
      })
    }
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    ftp_url=MapUtil.get(map,key="ftp_url").asInstanceOf[String]
    port=MapUtil.get(map,key="port").asInstanceOf[String]
    username=MapUtil.get(map,key="username").asInstanceOf[String]
    password=MapUtil.get(map,key="password").asInstanceOf[String]
    ftpFile=MapUtil.get(map,key="ftpFile").asInstanceOf[String]
    HDFSUrl=MapUtil.get(map,key="HDFSUrl").asInstanceOf[String]
    HDFSPath=MapUtil.get(map,key="HDFSPath").asInstanceOf[String]
    isFile=MapUtil.get(map,key="isFile").asInstanceOf[String]
    filterByName=MapUtil.get(map,key="filterByName").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url_str = new PropertyDescriptor().name("url_str").displayName("URL").description("IP of FTP server, such as 128.136.0.1 or ftp.ei.addfc.gak").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").description("Port of FTP server").required(false)
    val username = new PropertyDescriptor().name("username").displayName("USER_NAME").description("").required(false)
    val password = new PropertyDescriptor().name("password").displayName("PASSWORD").description("").required(false)
    val ftpFile = new PropertyDescriptor().name("ftpFile").displayName("FTP_File").description("The path of the file to the FTP server, such as /test/Ab/ or /test/Ab/test.txt").required(true)
    val HDFSUrl = new PropertyDescriptor().name("HDFSUrl").displayName("HDFSUrl").description("The URL of the HDFS file system, such as hdfs://10.0.88.70:9000").required(true)
    val HDFSPath = new PropertyDescriptor().name("HDFSPath").displayName("HDFSPath").description("The save path of the HDFS file system, such as /test/Ab/").required(true)
    val isFile = new PropertyDescriptor().name("isFile").displayName("isFile").description("Whether the path is a file or not, if true is filled in, only a single file specified by the path is downloaded. If false is filled in, all files under the folder are downloaded recursively.").required(true)
    val filterByName = new PropertyDescriptor().name("filterByName").displayName("filterByName").description("If you choose to download the entire directory, you can use this parameter to filter the files you need to download. " +
      "What you need to fill in here is standard Java regular expressions. For example, you need to download all files in the /A/ directory that end in .gz " +
      "You can fill in .*.gz here. If there are multiple screening conditions, need to use ; segmentation.").required(false)

    descriptor = filterByName :: descriptor
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
    ImageUtil.getImage("icon/ftp/loadFromFtpUrl.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.FtpGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
