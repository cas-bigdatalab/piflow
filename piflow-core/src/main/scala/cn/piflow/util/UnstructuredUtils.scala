package cn.piflow.util

import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileStatus, FileSystem, Path}

import java.io.{File, IOException}
import java.nio.file.Files.isRegularFile
import java.nio.file.{Files, Paths}
import scala.::
import scala.collection.mutable.ListBuffer

object UnstructuredUtils {

  def unstructuredHost(): String = {
    val unstructuredHost: String = PropertyUtil.getPropertyValue("unstructured.host")
    unstructuredHost
  }

  def unstructuredPort(): String = {
    var unstructuredPort: String = PropertyUtil.getPropertyValue("unstructured.port")
    if (unstructuredPort == null || unstructuredPort.isEmpty) unstructuredPort = "8000"
    unstructuredPort
  }


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

  def downloadFilesFromHdfs(hdfsFilePath: String) = {
    //    val hdfsFilePath = "/test;/test1/a.pdf" // HDFS路径，用分号隔开
    val localDir = FileUtil.LOCAL_FILE_PREFIX + IdGenerator.uuid() // 本地服务器目录
    val hdfsPaths = hdfsFilePath.split(";") // 将路径用分号分割成数组
    val conf = new Configuration()
    conf.set("fs.defaultFS", PropertyUtil.getPropertyValue("fs.defaultFS")) // 设置HDFS的namenode地址
    val fs = FileSystem.get(conf)
    hdfsPaths.foreach { hdfsPath =>
      downloadFiles(fs, new Path(hdfsPath), new Path(localDir))
    }
    fs.close()
    localDir
  }

  def downloadFiles(fs: FileSystem, srcPath: Path, localDir: Path): Unit = {
    val status = fs.getFileStatus(srcPath)
    if (status.isDirectory) {
      val files = fs.listStatus(srcPath)
      files.foreach { fileStatus =>
        val path = fileStatus.getPath
        if (fileStatus.isFile) {
          val localFilePath = new Path(localDir, path.getName)
          fs.copyToLocalFile(false, path, localFilePath)
        } else {
          val newLocalDir = new Path(localDir, path.getName)
          downloadFiles(fs, path, newLocalDir)
        }
      }
    } else {
      val localFilePath = new Path(localDir, srcPath.getName)
      fs.copyToLocalFile(false, srcPath, localFilePath)
    }
  }

  def getLocalFilePaths(filePaths: String) = {
    val paths = filePaths.split(";").toList
    paths.flatMap { path =>
      val file = new File(path)
      if (file.exists) {
        if (file.isDirectory) {
          listFiles(file)
        } else {
          List(file.getAbsolutePath).filterNot(_.endsWith(".crc"))
        }
      } else {
        println("filePath is empty")
        List.empty
      }
    }.filterNot(_.endsWith(".crc"))
  }

  def listFiles(directory: File): List[String] = {
    if (directory.exists && directory.isDirectory) {
      directory.listFiles.flatMap {
        case f if f.isFile => List(f.getAbsolutePath)
        case d if d.isDirectory => listFiles(d)
      }.toList.filterNot(_.endsWith(".crc"))  // 过滤掉以 .crc 结尾的文件路径
    } else {
      List.empty
    }
  }


  def deleteTempFiles(localDir: String) = {
    val directory = new File(localDir)
    if (directory.exists() && directory.isDirectory) {
      directory.listFiles.foreach { file =>
        file.delete()
      }
      directory.delete()
      println(s"Directory $localDir deleted successfully")
    } else {
      println(s"Directory $localDir does not exist or is not a directory")
    }
  }
}
