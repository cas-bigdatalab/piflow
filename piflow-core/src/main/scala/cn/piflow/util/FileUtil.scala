package cn.piflow.util

import java.io.{File, PrintWriter}

object FileUtil {

  def getJarFile(file:File): Array[File] ={
    val files = file.listFiles().filter(! _.isDirectory)
      .filter(t => t.toString.endsWith(".jar") )  //此处读取.txt and .md文件
    files ++ file.listFiles().filter(_.isDirectory).flatMap(getJarFile)
  }


  def writeFile(text: String, path: String) = {
    val writer = new PrintWriter(new File(path))
    writer.write(text)
    writer.close()
  }

  def main(args: Array[String]): Unit = {
    val classPath = PropertyUtil.getClassPath()

    val path = new File(classPath)
    getJarFile(path).foreach(println)

  }
}
