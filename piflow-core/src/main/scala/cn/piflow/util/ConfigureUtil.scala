package cn.piflow.util

import java.io.{File, FileInputStream, InputStream}
import java.util.Properties

import cn.piflow.util.FileUtil.getJarFile

object ConfigureUtil {

  val NOT_EXIST_FLAG = 0
  val EXIST_FLAG = 1

  def getCheckpointPath() : String = {
    val item = "checkPointPath"
    val hdfsFS = PropertyUtil.getPropertyValue("fs.defaultFS")
    val checkpointPath = hdfsFS + "/user/piflow/checkpoints/"

    val isCheckPointPathExist = H2Util.getFlag(item)
    if(isCheckPointPathExist == NOT_EXIST_FLAG){
      if(!HdfsUtil.exists(hdfsFS,checkpointPath)){
        HdfsUtil.mkdir(hdfsFS,checkpointPath)
      }
      H2Util.addFlag(item, EXIST_FLAG)
    }else{
      checkpointPath
    }

    checkpointPath
  }

  def getDebugPath():String = {
    val item = "debugPath"
    val hdfsFS = PropertyUtil.getPropertyValue("fs.defaultFS")
    val debugPath = hdfsFS + "/user/piflow/debug/"
    val isDebugPathExist = H2Util.getFlag(item)
    if(isDebugPathExist == NOT_EXIST_FLAG){
      if(!HdfsUtil.exists(hdfsFS,debugPath)){
        HdfsUtil.mkdir(hdfsFS,debugPath)
      }
      H2Util.addFlag(item, EXIST_FLAG)
    }else{
      debugPath
    }
    debugPath
  }

  def getIncrementPath():String = {
    val item = "incrementPath"
    val hdfsFS = PropertyUtil.getPropertyValue("fs.defaultFS")
    val incrementPath = hdfsFS + "/user/piflow/increment/"

    val isIncrementPathExist = H2Util.getFlag(item)
    if(isIncrementPathExist == NOT_EXIST_FLAG){
      if(!HdfsUtil.exists(hdfsFS,incrementPath)){
        HdfsUtil.mkdir(hdfsFS,incrementPath)
      }
      H2Util.addFlag(item, EXIST_FLAG)
    }else{
      incrementPath
    }
    incrementPath
  }

  def getPiFlowBundlePath():String = {
      var piflowBundleList = List[String]()
    val userDir = System.getProperty("user.dir")
    val path = new File(userDir)
    getJarFile(path).foreach(x => {

      if(x.getName == "piflow-server-0.9.jar")
        piflowBundleList = x.getAbsolutePath +: piflowBundleList

    })

    var piflowBundleJar = ""
    if(piflowBundleList.size > 0){
      piflowBundleJar = piflowBundleList(0)

      piflowBundleList.foreach( jarFile => {
        if(jarFile.contains("classpath")){
          piflowBundleJar =  jarFile
          println(piflowBundleJar)
          return piflowBundleJar
        }
      })

      piflowBundleList.foreach( jarFile => {
        if(jarFile.contains("piflow-server/target")){
          piflowBundleJar =  jarFile
          println(piflowBundleJar)
          return piflowBundleJar
        }
      })

    }
    println(piflowBundleJar)
    piflowBundleJar
  }

  def getYarnResourceManagerWebAppAddress() : String = {
    var yarnResourceManagerWebAppAddress = PropertyUtil.getPropertyValue("yarn.url")
    if(yarnResourceManagerWebAppAddress == null){
      var port = "8088"
      val yarnHostName = PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname")
      if(PropertyUtil.getPropertyValue("yarn.resourcemanager.webapp.address.port") != null){
        port = PropertyUtil.getPropertyValue("yarn.resourcemanager.webapp.address.port")
      }
      yarnResourceManagerWebAppAddress = "http://" + yarnHostName + ":" + port + "/ws/v1/cluster/apps/"
    }
    yarnResourceManagerWebAppAddress
  }

  def main(args: Array[String]): Unit = {
    val temp = getPiFlowBundlePath()

  }

}
