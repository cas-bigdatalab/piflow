package cn.piflow.conf.util

import scala.io.Source

object FileUtil {

  def fileReader(filePath : String) : String = {
    var str = ""
    val file = Source.fromFile(filePath)
    val iter = file.buffered
    while (iter.hasNext){
      val line = iter.head
      str += line
      iter.next()
    }
    file.close()
    str
  }

}
