package cn.piflow.api

import java.util.concurrent.CountDownLatch

import cn.piflow.Runner
import cn.piflow.conf.bean.{FlowBean, PropertyDescriptor}
import org.apache.spark.sql.SparkSession
import cn.piflow.conf.util.{ClassUtil, MapUtil, OptionUtil}
import cn.piflow.Process
import cn.piflow.api.util.PropertyUtil
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.launcher.{SparkAppHandle, SparkLauncher}

import scala.util.parsing.json.JSON

object API {

  /*def startFlow(flowJson : String):(String,Process) = {

    val map = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    //execute flow
    val spark = SparkSession.builder()
      .master(PropertyUtil.getPropertyValue("spark.master"))
      .appName(flowBean.name)
      .config("spark.deploy.mode",PropertyUtil.getPropertyValue("spark.deploy.mode"))
      .config("spark.hadoop.yarn.resourcemanager.hostname", PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname"))
      .config("spark.hadoop.yarn.resourcemanager.address", PropertyUtil.getPropertyValue("yarn.resourcemanager.address"))
      .config("spark.yarn.access.namenode", PropertyUtil.getPropertyValue("yarn.access.namenode"))
      .config("spark.yarn.stagingDir", PropertyUtil.getPropertyValue("yarn.stagingDir"))
      .config("spark.yarn.jars", PropertyUtil.getPropertyValue("yarn.jars"))
      //.config("spark.driver.memory", "1g")
      //.config("spark.executor.memory", "1g")
      //.config("spark.cores.max", "2")
      .config("spark.jars", PropertyUtil.getPropertyValue("piflow.bundle"))
      .config("hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .enableHiveSupport()
      .getOrCreate()


    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", PropertyUtil.getPropertyValue("checkpoint.path"))
      .start(flow);
    val applicationId = spark.sparkContext.applicationId
    //process.awaitTermination();
    //spark.close();
    new Thread( new WaitProcessTerminateRunnable(spark, process)).start()
    (applicationId,process)

  }*/
  def startFlow(flowJson : String):(String,SparkAppHandle) = {

    var appId:String = null
    val map = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]
    val flowMap = MapUtil.get(map, "flow").asInstanceOf[Map[String, Any]]
    val appName = MapUtil.get(flowMap,"name").asInstanceOf[String]

    val countDownLatch = new CountDownLatch(1)
    val launcher = new SparkLauncher
    val handle =launcher
      .setAppName(appName)
      .setMaster(PropertyUtil.getPropertyValue("spark.master"))
      .setDeployMode(PropertyUtil.getPropertyValue("spark.deploy.mode"))
      .setAppResource(PropertyUtil.getPropertyValue("piflow.bundle"))
      .setVerbose(true)
      .setConf("spark.hadoop.yarn.resourcemanager.hostname", PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname"))
      .setConf("spark.hadoop.yarn.resourcemanager.address", PropertyUtil.getPropertyValue("yarn.resourcemanager.address"))
      .setConf("spark.yarn.access.namenode", PropertyUtil.getPropertyValue("yarn.access.namenode"))
      .setConf("spark.yarn.stagingDir", PropertyUtil.getPropertyValue("yarn.stagingDir"))
      .setConf("spark.yarn.jars", PropertyUtil.getPropertyValue("yarn.jars"))
      .setConf("spark.jars", PropertyUtil.getPropertyValue("piflow.bundle"))
      .setConf("spark.hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .setConf("spark.driver.memory", "1g")
      .setConf("spark.executor.memory", "1g")
      .setConf("spark.cores.max", "1")
      .setMainClass("cn.piflow.api.StartFlowMain")
      .addAppArgs(flowJson)
      .startApplication( new SparkAppHandle.Listener {
        override def stateChanged(handle: SparkAppHandle): Unit = {
          appId = handle.getAppId
          val sparkAppState = handle.getState
          if(appId != null){
            println("Spark job with app id: " + appId + ",\t State changed to: " + sparkAppState)
          }else{
            println("Spark job's state changed to: " + sparkAppState)
          }
          if (handle.getState().isFinal){
            countDownLatch.countDown()
            println("Task is finished!")
          }
        }
        override def infoChanged(handle: SparkAppHandle): Unit = {
          //println("Info:" + handle.getState().toString)
        }
      })
    while (appId == null){
      Thread.sleep(1000)
    }
    //println("Task is executing, please wait...")
    //countDownLatch.await()
    //println("Task is finished!")

    /*launcher.launch()
    val sparkAppHandle : SparkAppHandle = launcher.startApplication()

    while(sparkAppHandle.getState != SparkAppHandle.State.FINISHED){
      Thread.sleep(10000)
      println("ApplicationId = " + sparkAppHandle.getAppId + "---Current State = " + sparkAppHandle.getState)
    }*/
    (appId, handle)
  }

  def stopFlow(process : SparkAppHandle): String = {
    process.stop()
    "ok"
  }

  def getFlowInfo(appID : String) : String = {

    val url = PropertyUtil.getPropertyValue("yarn.url") + appID
    val client = HttpClients.createDefault()
    val get:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(get)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
    str
  }

  def getStopInfo(bundle : String) : String = {
    try{

      val str = ClassUtil.findConfigurableStopInfo(bundle)
      str
    }catch{
      case ex : Exception => println(ex);throw ex
    }

  }

  def getAllGroups() = {
    val groups = ClassUtil.findAllGroups().mkString(",")
    """{"groups":"""" + groups + """"}"""
  }

}

class WaitProcessTerminateRunnable(spark : SparkSession, process: Process) extends Runnable  {
  override def run(): Unit = {
    process.awaitTermination()
    //spark.close()
  }
}
