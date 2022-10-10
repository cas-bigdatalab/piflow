package cn.piflow.util

import java.io.{FileInputStream, InputStream}
import java.util.Properties

object PropertyUtil {
  private val prop: Properties = new Properties()
  var fis: InputStream = null
  var path :String = ""
  var classPath:String = ""
  var scalaPath:String = ""
  var sparkJarPath:String = ""
  var visualDataDirectoryPath:String = ""
    try{
    //val path = Thread.currentThread().getContextClassLoader.getResource("config.properties").getPath
    //fis = this.getClass.getResourceAsStream("")
    val userDir = System.getProperty("user.dir")
    path = userDir + "/config.properties"
    classPath = userDir + "/classpath/"
    scalaPath = userDir + "/scala/"
    sparkJarPath = userDir + "/sparkJar/"
    visualDataDirectoryPath = getPropertyValue("fs.defaultFS") + "/visualDataDirectoryPath/"
    prop.load(new FileInputStream(path))
  } catch{
    case ex: Exception => ex.printStackTrace()
  }

  def getConfigureFile() : String = {
    path
  }

  def getClassPath():String = {
    classPath
  }

  def getScalaPath():String = {
    scalaPath
  }

  def getSpartJarPath():String = {
    sparkJarPath
  }

  def getVisualDataDirectoryPath():String = {
    visualDataDirectoryPath
  }

  def getPropertyValue(propertyKey: String): String ={
    val obj = prop.get(propertyKey)
    if(obj != null){
      return obj.toString
    }
    null
  }

  def getIntPropertyValue(propertyKey: String): Int ={
    val obj = prop.getProperty(propertyKey)
    if(obj != null){
      return obj.toInt
    }
    throw new NullPointerException
  }

}
