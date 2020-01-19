package cn.piflow.util

import java.io.{FileInputStream, InputStream}
import java.net.InetAddress
import java.util.Properties

object ServerIpUtil {
  private val prop: Properties = new Properties()
  var fis: InputStream = null
  var path :String = ""

    try{

    val userDir = System.getProperty("user.dir")
    path = userDir + "/server.ip"
    prop.load(new FileInputStream(path))
  } catch{
    case ex: Exception => ex.printStackTrace()
  }

  def getServerIpFile() : String = {
    path
  }


  def getServerIp(): String ={
    val obj = prop.get("server.ip")
    if(obj != null){
      return obj.toString
    }
    null
  }

  def main(args: Array[String]): Unit = {

    val ip = InetAddress.getLocalHost.getHostAddress
    //write ip to server.ip file
    FileUtil.writeFile("server.ip=" + ip, ServerIpUtil.getServerIpFile())
    println(ServerIpUtil.getServerIp())
  }
}
