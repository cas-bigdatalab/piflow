package cn.piflow.util

import java.io.{File, FileInputStream, InputStream}

import cn.piflow.util.FileUtil.getJarFile
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import com.alibaba.fastjson
import com.alibaba.fastjson.JSON

object ConfigureUtil {

  val NOT_EXIST_FLAG = 0
  val EXIST_FLAG = 1

  def getVisualizationPath() : String = {
    val item = "visualizationPath"
    val hdfsFS = PropertyUtil.getPropertyValue("fs.defaultFS")
    val visualizationPath = hdfsFS + "/user/piflow/visualization/"

    val isCheckPointPathExist = H2Util.getFlag(item)
    if(isCheckPointPathExist == NOT_EXIST_FLAG){
      if(!HdfsUtil.exists(hdfsFS,visualizationPath)){
        HdfsUtil.mkdir(hdfsFS,visualizationPath)
      }
      H2Util.addFlag(item, EXIST_FLAG)
    }else{
      visualizationPath
    }

    visualizationPath
  }

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

  def getTestDataPath() : String = {
    val item = "testDataPath"
    val hdfsFS = PropertyUtil.getPropertyValue("fs.defaultFS")
    val testDataPath = hdfsFS + "/user/piflow/testData/"

    val isCheckPointPathExist = H2Util.getFlag(item)
    if(isCheckPointPathExist == NOT_EXIST_FLAG){
      if(!HdfsUtil.exists(hdfsFS,testDataPath)){
        HdfsUtil.mkdir(hdfsFS,testDataPath)
      }
      H2Util.addFlag(item, EXIST_FLAG)
    }else{
      testDataPath
    }

    testDataPath
  }

  def getYarnResourceManagerAPI() : String = {
    var yarnURL = PropertyUtil.getPropertyValue("yarn.url")
    if(yarnURL == null){
      var port = "8088"
      val yarnHostName = PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname")
      if(PropertyUtil.getPropertyValue("yarn.resourcemanager.webapp.address.port") != null){
        port = PropertyUtil.getPropertyValue("yarn.resourcemanager.webapp.address.port")
      }
      yarnURL = "http://" + yarnHostName + ":" + port
    }
    val yarnAPI = yarnURL + "/ws/v1/cluster/"
    yarnAPI
  }

  def getYarnResourceManagerWebAppAddress() : String = {
    /*var yarnResourceManagerWebAppAddress = PropertyUtil.getPropertyValue("yarn.url")
    if(yarnResourceManagerWebAppAddress == null){
      var port = "8088"
      val yarnHostName = PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname")
      if(PropertyUtil.getPropertyValue("yarn.resourcemanager.webapp.address.port") != null){
        port = PropertyUtil.getPropertyValue("yarn.resourcemanager.webapp.address.port")
      }
      yarnResourceManagerWebAppAddress = "http://" + yarnHostName + ":" + port + "/ws/v1/cluster/apps/"
    }*/
    val yarnAPI = getYarnResourceManagerAPI()
    val webAppAddress = yarnAPI + "apps" + "/"
    webAppAddress
  }

  def getYarnResourceMatrics(): String = {
    /*var yarnResourceManagerWebAppAddress = PropertyUtil.getPropertyValue("yarn.url")
    if(yarnResourceManagerWebAppAddress == null){
      var port = "8088"
      val yarnHostName = PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname")
      if(PropertyUtil.getPropertyValue("yarn.resourcemanager.webapp.address.port") != null){
        port = PropertyUtil.getPropertyValue("yarn.resourcemanager.webapp.address.port")
      }
      yarnResourceManagerWebAppAddress = "http://" + yarnHostName + ":" + port + "/ws/v1/cluster/matrics/"
    }*/
    val yarnAPI = getYarnResourceManagerAPI()
    val matrics = yarnAPI + "metrics"
    matrics
  }

  def getYarnResourceManagerAppState(appId : String) : String = {
    val url = ConfigureUtil.getYarnResourceManagerWebAppAddress() + appId + "/state"
    val client = HttpClients.createDefault()
    val get:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(get)
    val entity = response.getEntity
    val stateJson = EntityUtils.toString(entity,"UTF-8")

    val flowJSONObject = JSON.parseObject(stateJson)
    val state = flowJSONObject.getString("state")
    state
  }

  def main(args: Array[String]): Unit = {
    val appId = "application_1627523264894_6792"
    val state = getYarnResourceManagerAppState(appId)
    println("Flow " + appId + "'s state is " + state )

  }

}
