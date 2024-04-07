package cn.piflow.util
object UnstructuredUtils {
  def deleteTempFile(filePath: String) = {
    var result = false
    FileUtil.deleteFile(filePath).recover {
      case ex: Exception =>
        println(s"Failed to delete file $filePath: ${ex.getMessage}")
    }.get
    result = true
    result
  }


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

  def downloadFileFromHdfs(filePath: String) = {
    var result = false
    //先检验file是否已经存在在本地
    val localFilePath = FileUtil.LOCAL_FILE_PREFIX + FileUtil.extractFileNameWithExtension(filePath)
    val exists = FileUtil.exists(localFilePath)
    if (!exists) {
      val hdfsFS = PropertyUtil.getPropertyValue("fs.defaultFS")
      result = FileUtil.downloadFileFromHdfs(hdfsFS, filePath)
    } else {
      result = true
    }
    result
  }


}
