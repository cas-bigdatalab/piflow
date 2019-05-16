package cn.piflow.api

import akka.actor.ActorSystem
import akka.http.scaladsl.Http
import akka.http.scaladsl.marshallers.sprayjson.SprayJsonSupport
import akka.http.scaladsl.model._
import akka.http.scaladsl.model.HttpMethods._
import akka.http.scaladsl.server.Directives
import akka.stream.ActorMaterializer
import cn.piflow.{FlowGroupExecution, ProjectExecution}
import cn.piflow.api.util.PropertyUtil
import cn.piflow.conf.util.{MapUtil, OptionUtil}
import com.typesafe.config.ConfigFactory

import scala.concurrent.Future
import scala.util.parsing.json.JSON
import org.apache.spark.launcher.SparkAppHandle
import org.h2.tools.Server
import spray.json.DefaultJsonProtocol


object HTTPService extends DefaultJsonProtocol with Directives with SprayJsonSupport{
  implicit val config = ConfigFactory.load()
  implicit val system = ActorSystem("PiFlowHTTPService", config)
  implicit val materializer = ActorMaterializer()
  implicit val executionContext = system.dispatcher
  var processMap = Map[String, SparkAppHandle]()
  var flowGroupMap = Map[String, FlowGroupExecution]()
  var projectMap = Map[String, ProjectExecution]()

  def toJson(entity: RequestEntity): Map[String, Any] = {
    entity match {
      case HttpEntity.Strict(_, data) =>{
        val temp = JSON.parseFull(data.utf8String)
        temp.get.asInstanceOf[Map[String, Any]]
      }
      case _ => Map()
    }
  }

  def route(req: HttpRequest): Future[HttpResponse] = req match {

   case HttpRequest(GET, Uri.Path("/"), headers, entity, protocol) => {
      Future.successful(HttpResponse(entity = "Get OK!"))
    }

   case HttpRequest(GET, Uri.Path("/flow/info"), headers, entity, protocol) => {

     val appID = req.getUri().query().getOrElse("appID","")
     if(!appID.equals("")){
       var result = API.getFlowInfo(appID)
       println("getFlowInfo result: " + result)
       if (result.equals("")){
         val yarnInfoJson = API.getFlowLog(appID)
         val map = OptionUtil.getAny(JSON.parseFull(yarnInfoJson)).asInstanceOf[Map[String, Any]]
         val appMap = MapUtil.get(map, "app").asInstanceOf[Map[String, Any]]
         val name = MapUtil.get(appMap,"name").asInstanceOf[String]
         val state = MapUtil.get(appMap,"state").asInstanceOf[String]
         var flowInfo = "{\"flow\":{\"id\":\"" + appID +
           "\",\"name\":\"" +  name +
           "\",\"state\":\"" +  state +
           "\",\"startTime\":\"" +  "" +
           "\",\"endTime\":\"" + "" +
           "\",\"stops\":[]}}"
       }
       Future.successful(HttpResponse(entity = result))
     }else{
       Future.successful(HttpResponse(entity = "appID is null or flow run failed!"))
     }

   }
   case HttpRequest(GET, Uri.Path("/flow/progress"), headers, entity, protocol) => {

     val appID = req.getUri().query().getOrElse("appID","")
     if(!appID.equals("")){
       var result = API.getFlowProgress(appID)
       println("getFlowProgress result: " + result)
       if (result.equals("NaN")){
         result = "0"
       }
       Future.successful(HttpResponse(entity = result))
     }else{
       Future.successful(HttpResponse(entity = "appID is null or flow run failed!"))
     }

   }

   case HttpRequest(GET, Uri.Path("/flow/log"), headers, entity, protocol) => {

     val appID = req.getUri().query().getOrElse("appID","")
     if(!appID.equals("")){
       val result = API.getFlowLog(appID)
       Future.successful(HttpResponse(entity = result))
     }else{
       Future.successful(HttpResponse(entity = "appID is null or flow does not exist!"))
     }

   }

   case HttpRequest(GET, Uri.Path("/flow/checkpoints"), headers, entity, protocol) => {

     val processID = req.getUri().query().getOrElse("processID","")
     if(!processID.equals("")){
       val result = API.getFlowCheckpoint(processID)
       Future.successful(HttpResponse(entity = result))
     }else{
       Future.successful(HttpResponse(entity = "processID is null or flow does not exist!"))
     }

   }

   case HttpRequest(GET, Uri.Path("/flow/debugData"), headers, entity, protocol) => {

     val processID = req.getUri().query().getOrElse("processID","")
     val stopName = req.getUri().query().getOrElse("stopName","")
     val port = req.getUri().query().getOrElse("port","default")
     if(!processID.equals("") && !stopName.equals()){
       val result = API.getFlowDebugData(processID, stopName, port)
       Future.successful(HttpResponse(entity = result))
     }else{
       Future.successful(HttpResponse(entity = "processID is null or stop does not have debug data!"))
     }

   }

   case HttpRequest(POST, Uri.Path("/flow/start"), headers, entity, protocol) =>{

     entity match {
       case HttpEntity.Strict(_, data) =>{
         var flowJson = data.utf8String
         flowJson = flowJson.replaceAll("}","}\n")
         //flowJson = JsonFormatTool.formatJson(flowJson)
         val (appId,pid,process) = API.startFlow(flowJson)
         processMap += (appId -> process)
         val result = "{\"flow\":{\"id\":\"" + appId + "\",\"pid\":\"" +  pid + "\"}}"
         Future.successful(HttpResponse(entity = result))
       }

       case ex => {
         println(ex)
         Future.successful(HttpResponse(entity = "Can not start flow!"))
         //Future.failed(/*new Exception("Can not start flow!")*/HttpResponse(entity = "Can not start flow!"))
       }
     }

   }

   case HttpRequest(POST, Uri.Path("/flow/stop"), headers, entity, protocol) =>{
      val data = toJson(entity)
      val appId  = data.get("appID").getOrElse("").asInstanceOf[String]
      if(appId.equals("") || !processMap.contains(appId)){
        Future.failed(new Exception("Can not found process Error!"))
      }else{

        processMap.get(appId) match {
          case Some(process) =>
            val result = API.stopFlow(appId, process)
            processMap.-(appId)
            Future.successful(HttpResponse(entity = result))
          case ex =>{
            println(ex)
            Future.successful(HttpResponse(entity = "Can not found process Error!"))
          }

        }

      }
    }

   case HttpRequest(GET, Uri.Path("/stop/info"), headers, entity, protocol) =>{
     val bundle = req.getUri().query().getOrElse("bundle","")
     if(bundle.equals("")){
       Future.failed(new Exception("Can not found bundle Error!"))
     }else{
       try{
         val stopInfo = API.getStopInfo(bundle)
         Future.successful(HttpResponse(entity = stopInfo))
       }catch {
         case ex => {
           println(ex)
           Future.successful(HttpResponse(entity = "Can not found stop properties Error!"))
         }
       }
     }
   }
   case HttpRequest(GET, Uri.Path("/stop/groups"), headers, entity, protocol) =>{

     try{
       val stopGroups = API.getAllGroups()
       Future.successful(HttpResponse(entity = stopGroups))
     }catch {
       case ex => {
         println(ex)
         Future.successful(HttpResponse(entity = "Can not found stop properties Error!"))
       }
     }
   }
   case HttpRequest(GET, Uri.Path("/stop/list"), headers, entity, protocol) =>{

     try{
       val stops = API.getAllStops()
       Future.successful(HttpResponse(entity = stops))
     }catch {
       case ex => {
         println(ex)
         Future.successful(HttpResponse(entity = "Can not found stop !"))
       }
     }

   }
   case HttpRequest(GET, Uri.Path("/stop/listWithGroup"), headers, entity, protocol) =>{

     try{
       val stops = API.getAllStopsWithGroup()
       Future.successful(HttpResponse(entity = stops))
     }catch {
       case ex => {
         println(ex)
         Future.successful(HttpResponse(entity = "Can not found stop !"))
       }
     }

   }

   case HttpRequest(POST, Uri.Path("/flowGroup/start"), headers, entity, protocol) =>{

     entity match {
       case HttpEntity.Strict(_, data) =>{
         var flowGroupJson = data.utf8String
         flowGroupJson = flowGroupJson.replaceAll("}","}\n")
         val flowGroupExecution = API.startFlowGroup(flowGroupJson)
         flowGroupMap += (flowGroupExecution.groupId() -> flowGroupExecution)
         val result = "{\"flowGroup\":{\"id\":\"" + flowGroupExecution.groupId() + "\"}}"
         Future.successful(HttpResponse(entity = result))
       }

       case ex => {
         println(ex)
         Future.successful(HttpResponse(entity = "Can not start flow group!"))
         //Future.failed(/*new Exception("Can not start flow!")*/HttpResponse(entity = "Can not start flow!"))
       }
     }

   }

   case HttpRequest(POST, Uri.Path("/flowGroup/stop"), headers, entity, protocol) =>{
     val data = toJson(entity)
     val groupId  = data.get("groupId").getOrElse("").asInstanceOf[String]
     if(groupId.equals("") || !flowGroupMap.contains(groupId)){
       Future.failed(new Exception("Can not found flowGroup Error!"))
     }else{

       flowGroupMap.get(groupId) match {
         case Some(flowGroupExecution) =>
           val result = API.stopFlowGroup(flowGroupExecution)
           flowGroupMap.-(groupId)
           Future.successful(HttpResponse(entity = "Stop FlowGroup Ok!!!"))
         case ex =>{
           println(ex)
           Future.successful(HttpResponse(entity = "Can not found FlowGroup Error!"))
         }

       }

     }
   }

   case HttpRequest(GET, Uri.Path("/flowGroup/info"), headers, entity, protocol) =>{

     val groupId = req.getUri().query().getOrElse("groupId","")
     if(!groupId.equals("")){
       var result = API.getFlowGroupInfo(groupId)
       println("getFlowGroupInfo result: " + result)

       Future.successful(HttpResponse(entity = result))
     }else{
       Future.successful(HttpResponse(entity = "groupId is null or flowGroup run failed!"))
     }
   }

   case HttpRequest(POST, Uri.Path("/project/start"), headers, entity, protocol) =>{

     entity match {
       case HttpEntity.Strict(_, data) =>{
         var projectJson = data.utf8String
         projectJson = projectJson.replaceAll("}","}\n")
         val projectExecution = API.startProject(projectJson)
         projectMap += (projectExecution.projectId() -> projectExecution)
         val result = "{\"project\":{\"id\":\"" + projectExecution.projectId()+ "\"}}"
         Future.successful(HttpResponse(entity = result))
       }

       case ex => {
         println(ex)
         Future.successful(HttpResponse(entity = "Can not start project!"))
         //Future.failed(/*new Exception("Can not start flow!")*/HttpResponse(entity = "Can not start flow!"))
       }
     }

   }

   case HttpRequest(POST, Uri.Path("/project/stop"), headers, entity, protocol) =>{
     val data = toJson(entity)
     val projectId  = data.get("projectId").getOrElse("").asInstanceOf[String]
     if(projectId.equals("") || !projectMap.contains(projectId)){
       Future.failed(new Exception("Can not found project Error!"))
     }else{

       projectMap.get(projectId) match {
         case Some(projectExecution) =>
           val result = API.stopProject(projectExecution)
           projectMap.-(projectId)
           Future.successful(HttpResponse(entity = "Stop project Ok!!!"))
         case ex =>{
           println(ex)
           Future.successful(HttpResponse(entity = "Can not found project Error!"))
         }

       }

     }
   }

   case HttpRequest(GET, Uri.Path("/project/info"), headers, entity, protocol) =>{

     val projectId = req.getUri().query().getOrElse("projectId","")
     if(!projectId.equals("")){
       var result = API.getProjectInfo(projectId)
       println("getProjectInfo result: " + result)

       Future.successful(HttpResponse(entity = result))
     }else{
       Future.successful(HttpResponse(entity = "projectId is null or project run failed!"))
     }
   }

    case _: HttpRequest =>
      Future.successful(HttpResponse(404, entity = "Unknown resource!"))
  }

  def run = {
    val ip = PropertyUtil.getPropertyValue("server.ip")
    val port = PropertyUtil.getIntPropertyValue("server.port")
    Http().bindAndHandleAsync(route, ip, port)
    println("Server:" + ip + ":" + port + " Started!!!")
  }

}

object Main {
  def main(argv: Array[String]):Unit = {
    HTTPService.run
    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort",PropertyUtil.getPropertyValue("h2.port")).start()
  }
}
