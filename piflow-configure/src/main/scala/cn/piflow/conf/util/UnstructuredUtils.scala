package cn.piflow.conf.util

object UnstructuredUtils {

  def extractFileNameWithExtension(filePath: String): String = {
    val lastSeparatorIndex = filePath.lastIndexOf('/')
    val lastBackslashIndex = filePath.lastIndexOf('\\')
    val separatorIndex = Math.max(lastSeparatorIndex, lastBackslashIndex)
    if (separatorIndex == -1) {
      filePath // 如果没有找到分隔符，则整个字符串就是文件名
    } else {
      filePath.substring(separatorIndex + 1) // 从分隔符后面开始截取，得到文件名
    }
  }

}
