package cn.piflow.util

import java.util.concurrent.CountDownLatch

import cn.piflow.Flow
import org.apache.spark.launcher.SparkAppHandle.State
import org.apache.spark.launcher.{SparkAppHandle, SparkLauncher}

/**
  * Created by xjzhu@cnic.cn on 4/30/19
  */
object FlowLauncher {

  def launch(flow: Flow) : SparkLauncher = {

    var flowJson = flow.getFlowJson()
    flowJson = flowJson.replaceAll("}","}\n")

    var appId : String = ""
    val countDownLatch = new CountDownLatch(1)
    val launcher = new SparkLauncher
    val sparkLauncher =launcher
      .setAppName(flow.getFlowName())
      .setMaster(PropertyUtil.getPropertyValue("spark.master"))
      .setDeployMode(PropertyUtil.getPropertyValue("spark.deploy.mode"))
      .setAppResource(PropertyUtil.getPropertyValue("piflow.bundle"))
      .setVerbose(true)
      .setConf("spark.jars", PropertyUtil.getPropertyValue("piflow.bundle"))
      .setConf("spark.hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .setConf("spark.driver.memory", flow.getDriverMemory())
      .setConf("spark.num.executors", flow.getExecutorNum())
      .setConf("spark.executor.memory", flow.getExecutorMem())
      .setConf("spark.executor.cores",flow.getExecutorCores())
      .addFile(PropertyUtil.getConfigureFile())
      .setMainClass("cn.piflow.api.StartFlowMain")
      .addAppArgs(flowJson)

    if(PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname") != null)
      sparkLauncher.setConf("spark.hadoop.yarn.resourcemanager.hostname", PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname"))
    if(PropertyUtil.getPropertyValue("yarn.resourcemanager.address") != null)
      sparkLauncher.setConf("spark.hadoop.yarn.resourcemanager.address", PropertyUtil.getPropertyValue("yarn.resourcemanager.address"))
    if(PropertyUtil.getPropertyValue("yarn.access.namenode") != null)
      sparkLauncher.setConf("spark.yarn.access.namenode", PropertyUtil.getPropertyValue("yarn.access.namenode"))
    if(PropertyUtil.getPropertyValue("yarn.stagingDir") != null)
      sparkLauncher.setConf("spark.yarn.stagingDir", PropertyUtil.getPropertyValue("yarn.stagingDir"))
    if(PropertyUtil.getPropertyValue("yarn.jars") != null)
      sparkLauncher.setConf("spark.yarn.jars", PropertyUtil.getPropertyValue("yarn.jars"))

    sparkLauncher
  }

}
