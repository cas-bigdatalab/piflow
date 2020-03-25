package cn.piflow.api

import java.net.InetAddress

import akka.actor.{ActorRef, ActorSystem, Props}
import akka.http.scaladsl.Http
import akka.http.scaladsl.marshallers.sprayjson.SprayJsonSupport
import akka.http.scaladsl.model._
import akka.http.scaladsl.model.HttpMethods._
import akka.http.scaladsl.server.Directives
import akka.stream.ActorMaterializer
import cn.piflow.{GroupExecution}
import cn.piflow.api.util.PropertyUtil
import cn.piflow.conf.util.{MapUtil, OptionUtil}
import cn.piflow.util._
import com.typesafe.akka.extension.quartz.QuartzSchedulerExtension
import com.typesafe.config.ConfigFactory

import scala.concurrent.Future
import scala.util.parsing.json.JSON
import org.apache.spark.launcher.SparkAppHandle
import org.flywaydb.core.Flyway
import org.flywaydb.core.api.FlywayException
import org.h2.tools.Server
import spray.json.DefaultJsonProtocol


object HTTPService extends DefaultJsonProtocol with Directives with SprayJsonSupport{
  implicit val config = ConfigFactory.load()
  implicit val system = ActorSystem("PiFlowHTTPService", config)
  implicit val materializer = ActorMaterializer()
  implicit val executionContext = system.dispatcher

  val scheduler = QuartzSchedulerExtension(system)
  var actorMap = Map[String, ActorRef]()


  var processMap = Map[String, SparkAppHandle]()
  var flowGroupMap = Map[String, GroupExecution]()
  //var projectMap = Map[String, GroupExecution]()

  val SUCCESS_CODE = 200
  val FAIL_CODE = 500
  val UNKNOWN_CODE = 404

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
      Future.successful(HttpResponse(SUCCESS_CODE, entity = "Get OK!"))
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

         var flowInfoMap = Map[String, Any]()
         flowInfoMap += ("id" -> appID)
         flowInfoMap += ("name" -> name)
         flowInfoMap += ("state" -> state)
         flowInfoMap += ("startTime" -> "")
         flowInfoMap += ("endTime" -> "")
         flowInfoMap += ("endTime" -> "")
         flowInfoMap += ("stops" -> List())
         result = JsonUtil.format(JsonUtil.toJson(Map("flow" -> flowInfoMap)))
       }
       Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "appID is null or flow run failed!"))
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
       Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "appID is null or flow run failed!"))
     }

   }

   case HttpRequest(GET, Uri.Path("/flow/log"), headers, entity, protocol) => {

     val appID = req.getUri().query().getOrElse("appID","")
     if(!appID.equals("")){
       val result = API.getFlowLog(appID)
       Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "appID is null or flow does not exist!"))
     }

   }

   case HttpRequest(GET, Uri.Path("/flow/checkpoints"), headers, entity, protocol) => {

     val appID = req.getUri().query().getOrElse("appID","")
     if(!appID.equals("")){
       val result = API.getFlowCheckpoint(appID)
       Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "appID is null or flow does not exist!"))
     }

   }

   case HttpRequest(GET, Uri.Path("/flow/debugData"), headers, entity, protocol) => {

     val appID = req.getUri().query().getOrElse("appID","")
     val stopName = req.getUri().query().getOrElse("stopName","")
     val port = req.getUri().query().getOrElse("port","default")
     if(!appID.equals("") && !stopName.equals()){
       val result = API.getFlowDebugData(appID, stopName, port)
       Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "appID is null or stop does not have debug data!"))
     }

   }

   case HttpRequest(POST, Uri.Path("/flow/start"), headers, entity, protocol) =>{

     entity match {
       case HttpEntity.Strict(_, data) =>{
         var flowJson = data.utf8String
//          flowJson = flowJson.replaceAll("}","}\n")
         //flowJson = JsonFormatTool.formatJson(flowJson)
         val (appId,process) = API.startFlow(flowJson)
         processMap += (appId -> process)
         val result = "{\"flow\":{\"id\":\"" + appId + "\"}}"
         Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
       }

       case ex => {
         println(ex)
         Future.successful(HttpResponse(FAIL_CODE, entity = "Can not start flow!"))
         //Future.failed(/*new Exception("Can not start flow!")*/HttpResponse(entity = "Can not start flow!"))
       }
     }

   }


   case HttpRequest(POST, Uri.Path("/flow/stop"), headers, entity, protocol) =>{
      val data = toJson(entity)
      val appId  = data.get("appID").getOrElse("").asInstanceOf[String]
      if(appId.equals("")){
        Future.failed(new Exception("Can not found application Error!"))
      }else{

        if(processMap.contains(appId)) {
          processMap.get(appId) match {
            case Some(process) =>
              val result = API.stopFlow(appId, process)
              processMap.-(appId)
              Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
            case ex => {
              println(ex)
              Future.successful(HttpResponse(FAIL_CODE, entity = "Can not found process Error!"))
            }

          }
        }else{
            val result = API.stopFlowOnYarn(appId)
            Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
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
         Future.successful(HttpResponse(SUCCESS_CODE, entity = stopInfo))
       }catch {
         case ex => {
           println(ex)
           Future.successful(HttpResponse(FAIL_CODE, entity = "getPropertyDescriptor or getIcon Method Not Implemented Error!"))
         }
       }
     }
   }
   case HttpRequest(GET, Uri.Path("/stop/groups"), headers, entity, protocol) =>{

     try{
       val stopGroups = API.getAllGroups()
       Future.successful(HttpResponse(SUCCESS_CODE, entity = stopGroups))
     }catch {
       case ex => {
         println(ex)
         Future.successful(HttpResponse(FAIL_CODE, entity = "getGroup Method Not Implemented Error!"))
       }
     }
   }
   case HttpRequest(GET, Uri.Path("/stop/list"), headers, entity, protocol) =>{

     try{
       val stops = API.getAllStops()
       Future.successful(HttpResponse(SUCCESS_CODE, entity = stops))
     }catch {
       case ex => {
         println(ex)
         Future.successful(HttpResponse(FAIL_CODE, entity = "Can not found stop !"))
       }
     }

   }
   case HttpRequest(GET, Uri.Path("/stop/listWithGroup"), headers, entity, protocol) =>{

     try{
       val stops = API.getAllStopsWithGroup()
       Future.successful(HttpResponse(SUCCESS_CODE, entity = stops))
     }catch {
       case ex => {
         println(ex)
         Future.successful(HttpResponse(FAIL_CODE, entity = "Can not found stop !"))
       }
     }

   }

   case HttpRequest(POST, Uri.Path("/group/start"), headers, entity, protocol) =>{

     entity match {
       case HttpEntity.Strict(_, data) =>{
         var flowGroupJson = data.utf8String
         val flowGroupExecution = API.startGroup(flowGroupJson)
         flowGroupMap += (flowGroupExecution.getGroupId() -> flowGroupExecution)
         val result = "{\"group\":{\"id\":\"" + flowGroupExecution.getGroupId() + "\"}}"
         Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
       }

       case ex => {
         println(ex)
         Future.successful(HttpResponse(FAIL_CODE, entity = "Can not start group!"))
       }
     }

   }


   case HttpRequest(POST, Uri.Path("/group/stop"), headers, entity, protocol) =>{
     val data = toJson(entity)
     val groupId  = data.get("groupId").getOrElse("").asInstanceOf[String]
     if(groupId.equals("") || !flowGroupMap.contains(groupId)){
       Future.failed(new Exception("Can not found flowGroup Error!"))
     }else{

       flowGroupMap.get(groupId) match {
         case Some(flowGroupExecution) =>
           val result = API.stopGroup(flowGroupExecution)
           flowGroupMap.-(groupId)
           Future.successful(HttpResponse(SUCCESS_CODE, entity = "Stop FlowGroup Ok!!!"))
         case ex =>{
           println(ex)
           Future.successful(HttpResponse(FAIL_CODE, entity = "Can not found FlowGroup Error!"))
         }

       }

     }
   }


   case HttpRequest(GET, Uri.Path("/group/info"), headers, entity, protocol) =>{

     val groupId = req.getUri().query().getOrElse("groupId","")
     if(!groupId.equals("")){
       var result = API.getFlowGroupInfo(groupId)
       println("getFlowGroupInfo result: " + result)

       Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "groupId is null or flowGroup run failed!"))
     }
   }

   case HttpRequest(GET, Uri.Path("/group/progress"), headers, entity, protocol) =>{

     val groupId = req.getUri().query().getOrElse("groupId","")
     if(!groupId.equals("")){
       var result = API.getFlowGroupProgress(groupId)
       println("getFlowGroupProgress result: " + result)

       Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "groupId is null or flowGroup progress exception!"))
     }
   }

   //schedule related API
   case HttpRequest(POST, Uri.Path("/schedule/start"), headers, entity, protocol) =>{

     entity match {
       case HttpEntity.Strict(_, data) =>{
         val dataMap = toJson(data.utf8String)

         val expression = dataMap.get("expression").getOrElse("").asInstanceOf[String]
         val scheduleInstance = dataMap.get("schedule").getOrElse(Map[String, Any]()).asInstanceOf[Map[String, Any]]

         val id : String = "schedule_" + IdGenerator.uuid() ;

         var scheduleType = ""
         if(!scheduleInstance.getOrElse("flow","").equals("")){
           scheduleType = ScheduleType.FLOW
         }else if(!scheduleInstance.getOrElse("group","").equals("")){
           scheduleType = ScheduleType.GROUP
         }else{
           Future.successful(HttpResponse(FAIL_CODE, entity = "Can not schedule, please check the json format!"))
         }
         val flowActor = system.actorOf(Props(new ExecutionActor(id,scheduleType)))
         scheduler.createSchedule(id,cronExpression = expression)
         scheduler.schedule(id,flowActor,JsonUtil.format(JsonUtil.toJson(scheduleInstance)))
         actorMap += (id -> flowActor)

         Future.successful(HttpResponse(SUCCESS_CODE, entity = id))
       }

       case ex => {
         println(ex)
         Future.successful(HttpResponse(FAIL_CODE, entity = "Can not start flow!"))
       }
     }

   }

   case HttpRequest(POST, Uri.Path("/schedule/stop"), headers, entity, protocol) =>{

     val data = toJson(entity)
     val scheduleId  = data.get("scheduleId").getOrElse("").asInstanceOf[String]
     if(scheduleId.equals("") || !actorMap.contains(scheduleId)){
       Future.failed(new Exception("Can not found scheduleId Error!"))
     }else{

       actorMap.get(scheduleId) match {
         case Some(actorRef) =>
           system.stop(actorRef)
           processMap.-(scheduleId)
           Future.successful(HttpResponse(SUCCESS_CODE, entity = "Stop schedule ok!"))
         case ex =>{
           println(ex)
           Future.successful(HttpResponse(FAIL_CODE, entity = "Can not found schedule Error!"))
         }

       }

     }

   }

   case HttpRequest(GET, Uri.Path("/schedule/info"), headers, entity, protocol) =>{

     val scheduleId = req.getUri().query().getOrElse("scheduleId","")
     if(!scheduleId.equals("")){
       var result = API.getScheduleInfo(scheduleId)
       println("getScheduleInfo result: " + result)

       Future.successful(HttpResponse(SUCCESS_CODE, entity = result))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "scheduleId is null or schedule info is error!"))
     }
   }

   case HttpRequest(GET, Uri.Path("/resource/info"), headers, entity, protocol) =>{

     val resourceInfo = API.getResourceInfo()
     if (resourceInfo != ""){
       Future.successful(HttpResponse(SUCCESS_CODE, entity = resourceInfo))
     }else{
       Future.successful(HttpResponse(FAIL_CODE, entity = "get resource info error!"))
     }

   }

   case _: HttpRequest =>
      Future.successful(HttpResponse(UNKNOWN_CODE, entity = "Unknown resource!"))
  }



  def run = {

    val ip = InetAddress.getLocalHost.getHostAddress
    //write ip to server.ip file
    FileUtil.writeFile("server.ip=" + ip, ServerIpUtil.getServerIpFile())

    val port = PropertyUtil.getIntPropertyValue("server.port")
    Http().bindAndHandleAsync(route, ip, port)
    println("Server:" + ip + ":" + port + " Started!!!")
  }

}

object Main {



  def flywayInit() = {

    val ip = InetAddress.getLocalHost.getHostAddress
    // Create the Flyway instance
    val flyway: Flyway = new Flyway();
    var url = "jdbc:h2:tcp://"+ip+":"+PropertyUtil.getPropertyValue("h2.port")+"/~/piflow"
    // Point it to the database
    flyway.setDataSource(url,null,null);
    flyway.setLocations("db/migrations");
    flyway.setEncoding("UTF-8");
    flyway.setTable("FLYWAY_SCHEMA_HISTORY");
    flyway.setBaselineOnMigrate(true);
    try {
      //Start the migration
      flyway.migrate();
    } catch {
      case e: FlywayException=>
        flyway.repair();
        print(e);
    }
  }
  def main(argv: Array[String]):Unit = {
    HTTPService.run
    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort",PropertyUtil.getPropertyValue("h2.port")).start()
    flywayInit();
  }
}
