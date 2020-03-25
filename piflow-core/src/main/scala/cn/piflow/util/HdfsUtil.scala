package cn.piflow.util

import java.io.{BufferedReader, IOException, InputStreamReader, PrintWriter}
import java.net.URI

import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FileStatus, FileSystem, Path}

object HdfsUtil {

  val conf : Configuration = new Configuration()
  var fs : FileSystem = null
  var hdfsInStream : FSDataInputStream = null

  def getFiles(filePath : String) : List[String] = {
    var fileList = List[String]()
    if(!filePath.equals("")){
      try{
        val fs:FileSystem = FileSystem.get(URI.create(filePath), new Configuration())
        val path = new org.apache.hadoop.fs.Path(filePath)
        val status = fs.listStatus(path)
        status.foreach{ s =>
          fileList = s.getPath.getName +: fileList
        }
      }catch{
        case ex:Exception => println(ex)
      }
    }
    fileList
  }


  def getLine(file : String) : String = {

    var line : String = ""
    var inputStream : FSDataInputStream = null
    var bufferedReader : BufferedReader = null

    try{
      inputStream = getFSDataInputStream(file)
      bufferedReader = new BufferedReader(new InputStreamReader(inputStream))
      line = bufferedReader.readLine();

    }catch{
      case ex : Exception => println(ex)
    }finally {
      if(bufferedReader != null){
        bufferedReader.close()
      }
      if(inputStream != null){
        close()
      }
    }
    line
  }

  def getLines(file : String) : String = {

    var result = ""
    var line : String = ""
    var inputStream : FSDataInputStream = null
    var bufferedReader : BufferedReader = null

    try{
      inputStream = getFSDataInputStream(file)
      bufferedReader = new BufferedReader(new InputStreamReader(inputStream))
      line = bufferedReader.readLine();
      while (line != null){
        result = result + " " + line
        line = bufferedReader.readLine()
      }

    }catch{
      case ex : Exception => println(ex)
    }finally {
      if(bufferedReader != null){
        bufferedReader.close()
      }
      if(inputStream != null){
        close()
      }
    }
    result
  }

  def saveLine(file : String, line: String) = {

    if(!file.equals("")){

      val fs:FileSystem = FileSystem.get(URI.create(file), new Configuration())
      val path = new org.apache.hadoop.fs.Path(file)
      val output = fs.create(path)
      val writer = new PrintWriter(output)
      try{

        writer.write(line)
        writer.write("\n")

      }catch{
        case ex:Exception => println(ex)
      }finally {
        writer.close()
      }

    }

  }

  def getFSDataInputStream(file : String) : FSDataInputStream = {

    var content = ""
    if(!file.equals("")){
      try{
        fs = FileSystem.get(URI.create(file), conf)
        hdfsInStream = fs.open(new org.apache.hadoop.fs.Path(file))

      }catch{
        case ex:Exception => println(ex)
      }
    }
    hdfsInStream
  }

  def close(): Unit = {
    try{
      if(hdfsInStream != null){
        hdfsInStream.close()
      }
      if(fs != null){
        fs.close()
      }
    }catch{
      case ex : IOException => println(ex)
    }
  }

  def getFilesInFolder(hdfsUrl: String, path: String): List[String] = {
    var result : List[String] = List()

    val config = new Configuration()
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)
    val listf = new Path(path)

    val statuses: Array[FileStatus] = fs.listStatus(listf)

    for (f <- statuses) {
      val fsPath = f.getPath().toString
      //println(fsPath)

      if (f.isDirectory) {
        result = fsPath::result
        getFilesInFolder(hdfsUrl, fsPath)

      } else{

        result = f.getPath.toString::result
      }
    }
    result
  }

  def exists(filePath : String) : Boolean = {
    var result : Boolean = false
    try{
      fs = FileSystem.get(conf)
      result = HdfsHelper.exists(fs, filePath)

    }catch{
      case ex : IOException => println(ex)
    }
    result
  }

  def createFile(filePath : String) : Boolean = {
    var result : Boolean = false
    try{
      fs = FileSystem.get(conf)
      result = HdfsHelper.createFile(fs, filePath)
    }catch{
      case ex : IOException => println(ex)
    }
    result
  }

  def exists(fsDefaultName: String, filePath : String) : Boolean = {
    var result : Boolean = false
    try{
      val conf = new Configuration()
      conf.set("fs.default.name",fsDefaultName)
      fs = FileSystem.get(conf)
      result = HdfsHelper.exists(fs, filePath)

    }catch{
      case ex : IOException => println(ex)
    }
    result
  }

  def mkdir(fsDefaultName: String, path:String) = {

    var result : Boolean = false
    try{

      val conf = new Configuration()
      conf.set("fs.default.name",fsDefaultName)
      fs = FileSystem.get(conf)

      result = HdfsHelper.createFolder(fs, path)

    }catch{
      case ex : IOException => println(ex)
    }
    result
  }

  def getCapacity() : Map[String, Any] = {
    val hdfsURL = PropertyUtil.getPropertyValue("fs.defaultFS")
    val conf = new Configuration()
    val fileSystem = FileSystem.get(new URI(hdfsURL),conf)
    val fsStatus = fileSystem.getStatus
    val capacity = fsStatus.getCapacity
    val remaining = fsStatus.getRemaining
    val used = fsStatus.getUsed
    val map = Map("capacity" -> capacity, "remaining" -> remaining, "used" -> used)
    map
  }

}
