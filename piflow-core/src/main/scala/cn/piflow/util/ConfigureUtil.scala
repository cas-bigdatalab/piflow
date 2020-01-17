package cn.piflow.util

import java.io.{FileInputStream, InputStream}
import java.util.Properties

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
    val userDir = System.getProperty("user.dir")
    var piflowBundlePath = PropertyUtil.getPropertyValue("piflow.bundle")
    if(piflowBundlePath == null){
      piflowBundlePath = userDir + "/lib/piflow-server-0.9.jar"
    }
    else
      piflowBundlePath = userDir + "/" + piflowBundlePath
    piflowBundlePath
  }

  def main(args: Array[String]): Unit = {
    val piflowBundlePath = getPiFlowBundlePath()
  }

}
