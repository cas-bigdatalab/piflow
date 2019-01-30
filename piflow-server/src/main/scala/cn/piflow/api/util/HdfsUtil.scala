package cn.piflow.api.util

import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileStatus, FileSystem, Path}

object HdfsUtil {

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

}
