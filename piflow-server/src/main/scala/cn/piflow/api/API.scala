package cn.piflow.api

import java.io.{File, FileOutputStream}
import java.net.URI
import java.text.SimpleDateFormat
import java.util.{Date, Properties}
import java.util.concurrent.CountDownLatch

import org.apache.spark.sql.SparkSession
import cn.piflow.conf.util.{ClassUtil, MapUtil, OptionUtil}
import cn.piflow.{FlowGroupExecution, Process, ProjectExecution, Runner}
import cn.piflow.api.util.PropertyUtil
import cn.piflow.conf.bean.{FlowGroupBean, ProjectBean}
import cn.piflow.util.{FlowState, H2Util, HdfsUtil}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileSystem, Path}
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost, HttpPut}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.launcher.{SparkAppHandle, SparkLauncher}

import scala.util.parsing.json.JSON

object API {

  def startProject(projectJson : String) = {

    println("StartProject API get json: \n" + projectJson )

    var appId:String = null
    val map = OptionUtil.getAny(JSON.parseFull(projectJson)).asInstanceOf[Map[String, Any]]
    val projectMap = MapUtil.get(map, "project").asInstanceOf[Map[String, Any]]

    //create flowGroup
    val projectBean = ProjectBean(map)
    val project = projectBean.constructProject()

    val projectExecution = Runner.create()
      .bind("checkpoint.path",PropertyUtil.getPropertyValue("checkpoint.path"))
      .bind("debug.path",PropertyUtil.getPropertyValue("debug.path"))
      .start(project);

    projectExecution

  }

  def stopProject(projectExecution : ProjectExecution): Unit ={
    projectExecution.stop()
  }

  def getProjectInfo(projectId : String) : String = {
    val projectInfo = H2Util.getProjectInfo(projectId)
    projectInfo
  }

  def startFlowGroup(flowGroupJson : String) = {

    println("StartFlowGroup API get json: \n" + flowGroupJson )

    var appId:String = null
    val map = OptionUtil.getAny(JSON.parseFull(flowGroupJson)).asInstanceOf[Map[String, Any]]
    val flowGroupMap = MapUtil.get(map, "group").asInstanceOf[Map[String, Any]]

    //create flowGroup
    val flowGroupBean = FlowGroupBean(map)
    val flowGroup = flowGroupBean.constructFlowGroup()

    val flowGroupExecution = Runner.create()
      .bind("checkpoint.path",PropertyUtil.getPropertyValue("checkpoint.path"))
      .bind("debug.path",PropertyUtil.getPropertyValue("debug.path"))
      .start(flowGroup);

    flowGroupExecution
  }

  def stopFlowGroup(flowGroupExecution : FlowGroupExecution): String ={
    flowGroupExecution.stop()
    "ok"
  }

  def getFlowGroupInfo(groupId : String) : String = {
    val flowGroupInfo = H2Util.getFlowGroupInfo(groupId)
    flowGroupInfo
  }

  def startFlow(flowJson : String):(String,SparkAppHandle) = {

    var appId:String = null
    val map = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]
    val flowMap = MapUtil.get(map, "flow").asInstanceOf[Map[String, Any]]
    val uuid = MapUtil.get(flowMap,"uuid").asInstanceOf[String]
    val appName = MapUtil.get(flowMap,"name").asInstanceOf[String]

    val dirverMem = flowMap.getOrElse("driverMemory","1g").asInstanceOf[String]
    val executorNum = flowMap.getOrElse("executorNumber","1").asInstanceOf[String]
    val executorMem= flowMap.getOrElse("executorMemory","1g").asInstanceOf[String]
    val executorCores = flowMap.getOrElse("executorCores","1").asInstanceOf[String]

    val (stdout, stderr) = getLogFile(uuid, appName)

    println("StartFlow API get json: \n" + flowJson )

    val countDownLatch = new CountDownLatch(1)
    val launcher = new SparkLauncher


    val sparkLauncher =launcher
      .setAppName(appName)
      .setMaster(PropertyUtil.getPropertyValue("spark.master"))
      .setDeployMode(PropertyUtil.getPropertyValue("spark.deploy.mode"))
      .setAppResource(PropertyUtil.getPropertyValue("piflow.bundle"))
      .setVerbose(true)
      .setConf("spark.hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .setConf("spark.driver.memory", dirverMem)
      .setConf("spark.num.executors",executorNum)
      .setConf("spark.executor.memory", executorMem)
      .setConf("spark.executor.cores",executorCores)
      .addFile(PropertyUtil.getConfigureFile())
      .setMainClass("cn.piflow.api.StartFlowMain")
      .addAppArgs(flowJson.stripMargin)
      //.redirectOutput(stdout)



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

      val handle = sparkLauncher.startApplication( new SparkAppHandle.Listener {
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
    /*while (handle.getAppId != null){
      appId = handle.getAppId
    }*/

    while (handle.getAppId == null){
      Thread.sleep(100)
    }
    appId = handle.getAppId


    (appId, handle)

  }

  def stopFlow(process : SparkAppHandle): String = {
    process.kill()
    "ok"
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
    val url = PropertyUtil.getPropertyValue("yarn.url") + appID + "/state"
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

    val url = PropertyUtil.getPropertyValue("yarn.url") + appID
    val client = HttpClients.createDefault()
    val get:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(get)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    str
  }

  def getFlowCheckpoint(appId:String) : String = {
    val checkpointPath = PropertyUtil.getPropertyValue("checkpoint.path").stripSuffix("/") + "/" + appId
    val checkpointList = HdfsUtil.getFiles(checkpointPath)
    """{"checkpoints":"""" + checkpointList.mkString(",") + """"}"""
  }


  def getFlowDebugData(appId : String, stopName : String, port : String) : String = {
    var result = ""
    val debugPath = PropertyUtil.getPropertyValue("debug.path").stripSuffix("/") + "/" + appId + "/" + stopName + "/" + port;
    val properties = new Properties()
    val hdfs = FileSystem.get(URI.create(debugPath), new Configuration())

    val fileList = HdfsUtil.getFilesInFolder(PropertyUtil.getPropertyValue("debug.path"), debugPath)

    fileList.filter(!_.equals("_SUCCESS")).foreach( file => {
      var stream = hdfs.open(new Path(file))
      def readLines = Stream.cons(stream.readLine(),Stream.continually(stream.readLine()))
      readLines.takeWhile( _ != null).foreach( line => {

        println(line)
        result += line + ","
      })
    })

    result = result.stripSuffix(",")

    val json = """{"debugInfo" : [ """ + result + """]}"""
    json
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
