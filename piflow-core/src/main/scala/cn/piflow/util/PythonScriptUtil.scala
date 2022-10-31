package cn.piflow.util

import java.io.InputStream
import java.util.Properties

object PythonScriptUtil {
  private val prop: Properties = new Properties()
  var fis: InputStream = null
  var path :String = ""

  try{

    val userDir = System.getProperty("user.dir")
    path = userDir + "/python/"

  } catch{
    case ex: Exception => ex.printStackTrace()
  }

  def getPath() : String = {
    path
  }

  def getJarPath() : String = {
    path + "/jar"
  }

  def main(args: Array[String]): Unit = {

    println(PythonScriptUtil.getPath())
  }
}
