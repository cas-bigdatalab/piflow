package cn.piflow.util

import java.io.{File, IOException, PrintWriter}
import java.nio.file.{Files, Paths}
import scala.io.Source
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileStatus, FileSystem, Path}

object FileUtil {

  val LOCAL_FILE_PREFIX = "/data/temp/files/"

  def downloadFileFromHdfs(fsDefaultName: String, hdfsFilePath: String) = {

    var fs: FileSystem = null
    var result: Boolean = false
    try {
      val conf = new Configuration()
      conf.set("fs.default.name", fsDefaultName)
      fs = FileSystem.get(conf)
      val hdfsPath = new Path(hdfsFilePath)
      val localPath = new Path(LOCAL_FILE_PREFIX + hdfsPath.getName()) // 本地目录和文件名

      if (fs.exists(hdfsPath)) {
        fs.copyToLocalFile(hdfsPath, localPath)
        println(s"File ${hdfsPath.getName()} downloaded successfully.")
        result = true
      } else {
        throw new Exception(s"File ${hdfsPath.getName()} does not exist in HDFS.")
      }
    } catch {
      case ex: IOException => println(ex)
    } finally {
      HdfsUtil.close(fs)
    }
    result
  }


  def exists(localFilePath: String): Boolean = {
    Files.exists(Paths.get(localFilePath))
  }

  def extractFileNameWithExtension(filePath: String): String = {
    val lastSeparatorIndex = filePath.lastIndexOf('/')
    val lastBackslashIndex = filePath.lastIndexOf('\\')
    val separatorIndex = Math.max(lastSeparatorIndex, lastBackslashIndex)
    if (separatorIndex == -1) {
      filePath  // 如果没有找到分隔符，则整个字符串就是文件名
    } else {
      filePath.substring(separatorIndex + 1)  // 从分隔符后面开始截取，得到文件名
    }
  }

  def getJarFile(file:File): Array[File] ={
    val files = file.listFiles().filter(! _.isDirectory)
      .filter(t => t.toString.endsWith(".jar") )  //此处读取.txt and .md文件
    files ++ file.listFiles().filter(_.isDirectory).flatMap(getJarFile)
  }


  def writeFile(text: String, path: String) = {

    val file = new File(path)
    if(!file.exists()){
      file.createNewFile()
    }
    val writer = new PrintWriter(new File(path))
    writer.write(text)
    writer.close()
  }

  def readFile(path : String) : String = {
    Source.fromFile(path).mkString("")
  }

  def main(args: Array[String]): Unit = {
    val classPath = PropertyUtil.getClassPath()

    val path = new File(classPath)
    getJarFile(path).foreach(println)

  }
}
