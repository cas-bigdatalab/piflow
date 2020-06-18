package cn.piflow.api

import java.io.{File, FileOutputStream}
import java.net.URI
import java.text.SimpleDateFormat
import java.util.{Date, Properties}
import java.util.concurrent.CountDownLatch

import org.apache.spark.sql.SparkSession
import cn.piflow.conf.util.{ClassUtil, MapUtil, OptionUtil, PluginManager, ScalaExecutorUtil}
import cn.piflow.{GroupExecution, Process, Runner}
import cn.piflow.conf.bean.{FlowBean, GroupBean}
import cn.piflow.util._
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPut}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.launcher.SparkAppHandle

import scala.util.parsing.json.JSON
import scala.util.control.Breaks._
import scala.collection.mutable.{Map => MMap}

object API {

  def addPlugin(pluginManager:PluginManager, pluginName : String) : Boolean = {
    var result = false
    val classpathFile = new File(pluginManager.getPluginPath())
    val jarFile = FileUtil.getJarFile(classpathFile)
    breakable{
      jarFile.foreach( i => {
        if(i.getName.equals(pluginName)) {

          pluginManager.unloadPlugin(i.getAbsolutePath)
          pluginManager.loadPlugin(i.getAbsolutePath)
          H2Util.addPlugin(pluginName)
          result = true
          break
        }
      })
    }
    result
  }

  def removePlugin(pluginManager:PluginManager, pluginName : String) : Boolean = {
    var result = false
    val classpathFile = new File(pluginManager.getPluginPath())
    val jarFile = FileUtil.getJarFile(classpathFile)
    breakable{
      jarFile.foreach( i => {
        println(i.getAbsolutePath)
        if(i.getName.equals(pluginName)) {
          pluginManager.unloadPlugin(i.getAbsolutePath)
          H2Util.removePlugin(pluginName)
          result = true
          break
        }
      })
    }
    result
  }

  def getConfigurableStopInPlugin(pluginManager:PluginManager, pluginName : String) : String = {
    var bundleList = List[String]()
    val stops = pluginManager.getPluginConfigurableStops(pluginName)
    stops.foreach(s => {
      bundleList = s.getClass.getName +: bundleList
    })

    """{"bundles":"""" + bundleList.mkString(",") + """"}"""
  }

  def getResourceInfo() : String = {

    try{
      val matricsURL = ConfigureUtil.getYarnResourceMatrics()
      val client = HttpClients.createDefault()
      val get:HttpGet = new HttpGet(matricsURL)

      val response:CloseableHttpResponse = client.execute(get)
      val entity = response.getEntity
      val str = EntityUtils.toString(entity,"UTF-8")
      val yarnInfo = OptionUtil.getAny(JSON.parseFull(str)).asInstanceOf[Map[String, Any]]
      val matricInfo = MapUtil.get(yarnInfo, "clusterMetrics").asInstanceOf[Map[String, Any]]


      val cpuInfo = Map(
        "totalVirtualCores" -> matricInfo.getOrElse("totalVirtualCores",""),
        "allocatedVirtualCores" -> matricInfo.getOrElse("allocatedVirtualCores",""),
        "reservedVirtualCores" -> matricInfo.getOrElse("reservedVirtualCores","")
      )
      val memoryInfo = Map(
        "totalMB" -> matricInfo.getOrElse("totalMB",""),
        "allocatedMB" -> matricInfo.getOrElse("allocatedMB",""),
        "reservedMB" -> matricInfo.getOrElse("reservedMB","")
      )
      val hdfsInfo = HdfsUtil.getCapacity()

      val map = Map("cpu" -> cpuInfo, "memory" -> memoryInfo, "hdfs" -> hdfsInfo)
      val resultMap = Map("resource" -> map)

      JsonUtil.format(JsonUtil.toJson(resultMap))
    }catch{
      case ex:Exception => ""
    }

  }

  def getScheduleInfo(scheduleId : String) : String = {

    val scheduleInfo = H2Util.getScheduleInfo(scheduleId)
    scheduleInfo
  }

  def startGroup(groupJson : String) = {

    println("StartGroup API get json: \n" + groupJson )

    var appId:String = null
    val map = OptionUtil.getAny(JSON.parseFull(groupJson)).asInstanceOf[Map[String, Any]]
    val flowGroupMap = MapUtil.get(map, "group").asInstanceOf[Map[String, Any]]

    //create flowGroup
    val groupBean = GroupBean(map)
    val group = groupBean.constructGroup()

    val flowGroupExecution = Runner.create()
      .bind("checkpoint.path",ConfigureUtil.getCheckpointPath())
      .bind("debug.path",ConfigureUtil.getDebugPath())
      .start(group);

    flowGroupExecution
  }

  def stopGroup(flowGroupExecution : GroupExecution): String ={
    flowGroupExecution.stop()
    "ok"
  }

  def getFlowGroupInfo(groupId : String) : String = {
    val flowGroupInfo = H2Util.getFlowGroupInfo(groupId)
    flowGroupInfo
  }
  def getFlowGroupProgress(flowGroupID : String) : String = {
    val progress = H2Util.getGroupProgressPercent(flowGroupID)
    progress
  }

  def startFlow(flowJson : String):(String,SparkAppHandle) = {

    var appId:String = null
    val flowMap = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]


    //create flow
    val flowBean = FlowBean(flowMap)
    val flow = flowBean.constructFlow()

    val uuid = flow.getUUID()
    val appName = flow.getFlowName()
    val (stdout, stderr) = getLogFile(uuid, appName)

    println("StartFlow API get json: \n" + flowJson )

    val countDownLatch = new CountDownLatch(1)

    val handle = FlowLauncher.launch(flow).startApplication( new SparkAppHandle.Listener {
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


    while (handle.getAppId == null){
      Thread.sleep(100)
    }
    appId = handle.getAppId


    (appId, handle)

  }

  def stopFlow(appID : String, process : SparkAppHandle) : String = {

    //yarn application kill appId
    stopFlowOnYarn(appID)

    //process kill
    process.kill()

    //update db
    H2Util.updateFlowState(appID, FlowState.KILLED)
    H2Util.updateFlowFinishedTime(appID, new Date().toString)

    "ok"
  }

  def stopFlowOnYarn(appID : String) : String = {
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
    str
  }

  def getFlowInfo(appID : String) : String = {
    val flowInfo = H2Util.getFlowInfo(appID)
    flowInfo
  }

  def getFlowProgress(appID : String) : String = {
    val progress = H2Util.getFlowProgress(appID)
    progress
  }

  def getFlowLog(appID : String) : String = {

    val url = ConfigureUtil.getYarnResourceManagerWebAppAddress() + appID
    val client = HttpClients.createDefault()
    val get:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(get)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    str
  }

  def getFlowCheckpoint(appId:String) : String = {
    val checkpointPath = ConfigureUtil.getCheckpointPath().stripSuffix("/") + "/" + appId
    val checkpointList = HdfsUtil.getFiles(checkpointPath)
    """{"checkpoints":"""" + checkpointList.mkString(",") + """"}"""
  }


  def getFlowDebugData(appId : String, stopName : String, port : String) : String = {

    val debugPath :String = ConfigureUtil.getDebugPath().stripSuffix("/") + "/" + appId + "/" + stopName + "/" + port;
    val schema = HdfsUtil.getLine(debugPath + "_schema")
    val result ="{\"schema\":\"" + schema+ "\", \"debugDataPath\": \""+ debugPath + "\"}"
    result
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

  def getAllStops() : String = {
    var stops : List[String] = List()
    val stopList = ClassUtil.findAllConfigurableStop()
    stopList.foreach(s => stops =  s.getClass.getName +: stops )
    """{"stops":"""" + stops.mkString(",") + """"}"""
  }

  def getAllStopsWithGroup() : String = {

    var resultList:List[String] = List()
    var stops = List[Tuple2[String,String]]()
    val configurableStopList = ClassUtil.findAllConfigurableStop()
    configurableStopList.foreach(s => {
      //generate (group,bundle) pair and put into stops
      val groupList = s.getGroup()
      groupList.foreach(group => {
        val tuple = (group , s.getClass.getName)
        stops =   tuple +: stops
      })
    })

    //(CommonGroup,List((CommonGroup,cn.piflow.bundle.common.Fork),(CommonGroup,cn.piflow.bundle.common.Merge),(...)))
    val groupsInfo = stops.groupBy(_._1)
    groupsInfo.foreach(group => {
      val stopList = group._2
      stopList.foreach( groupAndstopPair => {
        println(groupAndstopPair._1 + ":\t\t" + groupAndstopPair._2)
        var groupAndstop = groupAndstopPair._1 + ":" + groupAndstopPair._2
        resultList = groupAndstop +: resultList
      })
    })
    println("Total stop count : " + stops.size)

    """{"stopWithGroup":"""" + resultList.mkString(",") + """"}"""
  }

  private def getLogFile(uuid : String, appName : String) : (File,File) = {
    val now : Date = new Date()
    val dataFormat : SimpleDateFormat = new SimpleDateFormat("yyyy-MM-dd_HH:mm:ss")
    val nowDate = dataFormat.format(now)

    val stdoutPathString = PropertyUtil.getPropertyValue("log.path") + "/" + appName + "_" + uuid + "_stdout_" + nowDate
    val stdout = new File(stdoutPathString)

    val stderrPathString = PropertyUtil.getPropertyValue("log.path") + "/" + appName + "_" + uuid + "_stderr_" + nowDate
    val stderr = new File(stderrPathString)

    (stdout, stderr)
  }

}

class WaitProcessTerminateRunnable(spark : SparkSession, process: Process) extends Runnable  {
  override def run(): Unit = {
    process.awaitTermination()
    //spark.close()
  }
}
