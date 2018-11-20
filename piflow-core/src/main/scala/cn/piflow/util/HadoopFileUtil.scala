package cn.piflow.util

import java.net.URI

import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.FileSystem

object HadoopFileUtil {

  def getFileInHadoopPath(filePath : String) : List[String] = {
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

}
