package cn.piflow.util

import java.io.{BufferedReader, IOException, InputStreamReader, PrintWriter}
import java.net.URI

import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileStatus, FileSystem, Path}

object HdfsUtil {

  def getFiles(filePath : String) : List[String] = {
    var fs:FileSystem = null
    var fileList = List[String]()
    if(!filePath.equals("")){
      try{
        fs = FileSystem.get(URI.create(filePath), new Configuration())
        val path = new org.apache.hadoop.fs.Path(filePath)
        val status = fs.listStatus(path)
        status.foreach{ s =>
          fileList = s.getPath.getName +: fileList
        }
      }catch{
        case ex:Exception => println(ex)
      }finally {
        close(fs)
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
      close(bufferedReader)
      close(inputStream)
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
      close(bufferedReader)
      close(inputStream)
    }
    result
  }

  def saveLine(file : String, line: String) = {

    var fs:FileSystem = null
    var writer : PrintWriter = null
    var output : FSDataOutputStream = null
    if(!file.equals("")){

      try{
        fs = FileSystem.get(URI.create(file), new Configuration())
        output = fs.create(new Path(file))
        writer = new PrintWriter(output)
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
    var hdfsInStream : FSDataInputStream = null
    if(!file.equals("")){
      try{
        val fs = FileSystem.get(URI.create(file), new Configuration())
        hdfsInStream = fs.open(new org.apache.hadoop.fs.Path(file))

      }catch{
        case ex:Exception => println(ex)
      }
    }
    return hdfsInStream
  }

  def close(hdfsInStream : FSDataInputStream): Unit = {
    try{
      if(hdfsInStream != null){
        hdfsInStream.close()
      }

    }catch{
      case ex : IOException => println(ex)
    }
  }

  def close(fs : FileSystem): Unit = {
    try{
      if(fs != null){
        fs.close()
      }

    }catch{
      case ex : IOException => println(ex)
    }
  }

  def close(br : BufferedReader): Unit = {
    try{
      if(br != null){
        br.close()
      }

    }catch{
      case ex : IOException => println(ex)
    }
  }



  def getFilesInFolder(fsDefaultName: String, path: String): List[String] = {
    var result : List[String] = List()

    val config = new Configuration()
    config.set("fs.defaultFS",fsDefaultName)
    val fs = FileSystem.get(config)
    val listf = new Path(path)

    val statuses: Array[FileStatus] = fs.listStatus(listf)

    for (f <- statuses) {
      val fsPath = f.getPath().toString
      //println(fsPath)

      if (f.isDirectory) {
        result = fsPath::result
        getFilesInFolder(fsDefaultName, fsPath)

      } else{

        result = f.getPath.toString::result
      }
    }
    result
  }

  def exists(filePath : String) : Boolean = {
    var fs : FileSystem = null
    var result : Boolean = false
    try{
      val hdfsFS = PropertyUtil.getPropertyValue("fs.defaultFS")

      fs = FileSystem.get(new URI(hdfsFS), new Configuration())
      result = HdfsHelper.exists(fs, filePath)

    }catch{
      case ex : IOException => println(ex)
    }finally {
      close(fs)
    }

    result
  }

  def createFile(filePath : String) : Boolean = {
    var fs : FileSystem = null
    var result : Boolean = false
    try{
      val hdfsFS = PropertyUtil.getPropertyValue("fs.defaultFS")
      fs = FileSystem.get(new URI(hdfsFS), new Configuration())
      result = HdfsHelper.createFile(fs, filePath)
    }catch{
      case ex : IOException => println(ex)

    }finally {
      close(fs)
    }
    result
  }

  def exists(fsDefaultName: String, filePath : String) : Boolean = {
    var fs : FileSystem = null
    var result : Boolean = false
    try{
      val conf = new Configuration()
      conf.set("fs.default.name",fsDefaultName)
      fs = FileSystem.get(conf)
      result = HdfsHelper.exists(fs, filePath)

    }catch{
      case ex : IOException => println(ex)
    }finally {
      close(fs)
    }
    result
  }

  def mkdir(fsDefaultName: String, path:String) = {
    var fs : FileSystem = null
    var result : Boolean = false
    try{

      val conf = new Configuration()
      conf.set("fs.default.name",fsDefaultName)
      fs = FileSystem.get(conf)

      result = HdfsHelper.createFolder(fs, path)

    }catch{
      case ex : IOException => println(ex)

    }finally {
      close(fs)
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

  def main(args: Array[String]): Unit = {
    val path = "hdfs://10.0.86.191:9000/user/piflow/debug/test/test_schema"

    //val t = createFile(path)
    saveLine(path,"xjzhu,xjzhu,xjzhu")

  }

}
