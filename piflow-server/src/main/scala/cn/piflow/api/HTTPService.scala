package cn.piflow.api

import akka.actor.ActorSystem
import akka.http.scaladsl.Http
import akka.http.scaladsl.marshallers.sprayjson.SprayJsonSupport
import akka.http.scaladsl.model._
import akka.http.scaladsl.model.HttpMethods._
import akka.http.scaladsl.server.Directives
import akka.stream.ActorMaterializer
import cn.piflow.api.util.PropertyUtil
import com.typesafe.config.ConfigFactory

import scala.concurrent.Future
import scala.util.parsing.json.JSON
import org.apache.spark.launcher.SparkAppHandle
import spray.json.DefaultJsonProtocol


object HTTPService extends DefaultJsonProtocol with Directives with SprayJsonSupport{
  implicit val system = ActorSystem("HTTPService", ConfigFactory.load())
  implicit val materializer = ActorMaterializer()
  implicit val executionContext = system.dispatcher
  var processMap = Map[String, SparkAppHandle]()

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
       val result = API.getFlowInfo(appID)
       Future.successful(HttpResponse(entity = result))
     }else{
       Future.successful(HttpResponse(entity = "appID is null or not existed!"))
     }

   }

   case HttpRequest(POST, Uri.Path("/flow/start"), headers, entity, protocol) =>{

     entity match {
       case HttpEntity.Strict(_, data) =>{
         var flowJson = data.utf8String
         flowJson = flowJson.replaceAll("}","}\n")
         val (appId,process) = API.startFlow(flowJson)
         processMap += (appId -> process)
         Future.successful(HttpResponse(entity = appId))
       }

       case ex => {
         println(ex)
         Future.failed(new Exception("Can not start flow!"))
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
            val result = API.stopFlow(process)
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
  }
}
