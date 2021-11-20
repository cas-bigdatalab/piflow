package cn.piflow.util

import java.io.File
import java.util.Date
import java.util.concurrent.CountDownLatch

import cn.piflow.Flow
import org.apache.hadoop.security.SecurityUtil
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPut}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.launcher.SparkLauncher

/**
  * Created by xjzhu@cnic.cn on 4/30/19
  */
object FlowLauncher {

  def launch(flow: Flow) : SparkLauncher = {

    var flowJson = flow.getFlowJson()
    println("FlowLauncher json:" + flowJson)

    val flowFileName = flow.getFlowName() + new Date().getTime
    val flowFile = FlowFileUtil.getFlowFilePath(flowFileName)
    FileUtil.writeFile(flowJson, flowFile)
    //val flowJsonencryptAES = SecurityUtil.encryptAES(flowJson)

    var appId : String = ""
    val countDownLatch = new CountDownLatch(1)
    val launcher = new SparkLauncher
    val sparkLauncher =launcher
      .setAppName(flow.getFlowName())
      .setMaster(PropertyUtil.getPropertyValue("spark.master"))
      //.setDeployMode(PropertyUtil.getPropertyValue("spark.deploy.mode"))
      .setAppResource(ConfigureUtil.getPiFlowBundlePath())
      .setVerbose(true)
      .setConf("spark.driver.memory", flow.getDriverMemory())
      .setConf("spark.executor.instances", flow.getExecutorNum())
      .setConf("spark.executor.memory", flow.getExecutorMem())
      .setConf("spark.executor.cores",flow.getExecutorCores())
      .addFile(PropertyUtil.getConfigureFile())
      .addFile(ServerIpUtil.getServerIpFile())
      .addFile(flowFile)
      .setMainClass("cn.piflow.api.StartFlowMain")
      .addAppArgs(flowFileName)

    val sparkMaster = PropertyUtil.getPropertyValue("spark.master")
    if(sparkMaster.equals("yarn")){
      sparkLauncher.setDeployMode(PropertyUtil.getPropertyValue("spark.deploy.mode"))
      sparkLauncher.setConf("spark.hadoop.yarn.resourcemanager.hostname", PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname"))
    }

    //add plugin jars for application
    val pluginOnList = H2Util.getPluginOn()
    val classPath = PropertyUtil.getClassPath()
    val classPathFile = new File(classPath)
    if(classPathFile.exists()){
      FileUtil.getJarFile(new File(classPath)).foreach(f => {
        pluginOnList.foreach( pluginName => {
          if(pluginName == f.getName){
            println(f.getPath)
            sparkLauncher.addJar(f.getPath)
          }
        })
      })
    }


    //add sparkJar to spark cluster
    val sparkJarList = H2Util.getSparkJarOn()
    val sparkJarPath = PropertyUtil.getSpartJarPath()
    val sparkJarPathFile = new File(sparkJarPath)
    if(sparkJarPathFile.exists()){
      FileUtil.getJarFile(new File(sparkJarPath)).foreach(f => {
        sparkJarList.foreach( sparkJarName => {
          if(sparkJarName == f.getName){
            println("Load " + f.getPath + "to spark cluster!!!")
            sparkLauncher.addJar(f.getPath)
          }
        })

      })
    }

    val scalaPath = PropertyUtil.getScalaPath()
    val scalaPathFile = new File(scalaPath)
    if(scalaPathFile.exists()){
      FileUtil.getJarFile(new File(scalaPath)).foreach(f => {
        println("Load scala Jar: " + f.getPath )
        sparkLauncher.addJar(f.getPath)
      })
    }

    sparkLauncher
  }

  def stop(appID: String) = {

    println("Stop Flow !!!!!!!!!!!!!!!!!!!!!!!!!!")
    //yarn application kill appId
    val url = ConfigureUtil.getYarnResourceManagerWebAppAddress() + appID + "/state"
    val client = HttpClients.createDefault()
    val put:HttpPut = new HttpPut(url)
    val body ="{\"state\":\"KILLED\"}"
    put.addHeader("Content-Type", "application/json")
    put.setEntity(new StringEntity(body))
    val response:CloseableHttpResponse = client.execute(put)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")

    //update db
    println("Update flow state after Stop Flow !!!!!!!!!!!!!!!!!!!!!!!!!!")
    H2Util.updateFlowState(appID, FlowState.KILLED)
    H2Util.updateFlowFinishedTime(appID, new Date().toString)

    "ok"
  }

}
