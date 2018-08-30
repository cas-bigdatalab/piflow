package cn.piflow.api

import java.io.File
import java.util.concurrent.CompletionStage

import akka.actor.ActorSystem
import akka.http.scaladsl.Http
import akka.http.scaladsl.common.{EntityStreamingSupport, JsonEntityStreamingSupport}
import akka.http.scaladsl.marshallers.sprayjson.SprayJsonSupport
import akka.http.scaladsl.model._
import akka.http.scaladsl.model.HttpMethods._
import akka.http.scaladsl.server.Directives
import akka.stream.ActorMaterializer
import akka.stream.scaladsl.{FileIO, Framing}
import akka.util.ByteString
import cn.piflow.api.util.PropertyUtil
import com.typesafe.config.ConfigFactory

import scala.concurrent.Future
import scala.util.parsing.json.JSON
import cn.piflow.Process
import org.apache.http.util.EntityUtils
import spray.json.DefaultJsonProtocol


object HTTPService extends DefaultJsonProtocol with Directives with SprayJsonSupport{
  implicit val system = ActorSystem("HTTPService", ConfigFactory.load())
  implicit val materializer = ActorMaterializer()
  implicit val executionContext = system.dispatcher
  implicit val jsonStreamingSupport : JsonEntityStreamingSupport = EntityStreamingSupport.json
  var processMap = Map[String, Process]()

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

   case HttpRequest(POST, Uri.Path("/flow/start"), headers, entity, protocol) =>{

     /*entity.getDataBytes().runFold(ByteString.empty, ByteString.materializer).thenCompose(r => {
       val jsonString = r.utf8String
     })*/

     entity match {
       case HttpEntity.Strict(_, data) =>{
         val process = API.startFlow(data.utf8String)
         processMap += (process.pid() -> process)
         Future.successful(HttpResponse(entity = process.pid()))
       }
       case HttpEntity.Default(_,contentLength,source)=>{

         //source.runFoldAsync(ByteString.empty,materializer)
         //entity.dataBytes.runWith(FileIO.toPath(new File("/opt/flow.json").toPath))
         //val temp = entity.dataBytes.runWith(Sink.head).map(_.utf8String)
         //entity.toStrict(3000,materializer).whenComplete((strict, th) => {println(strict.getData.utf8String)})
         val process = API.startFlow("")
         processMap += (process.pid() -> process)
         Future.successful(HttpResponse(entity = process.pid()))

       }
       case _ => Future.failed(new Exception("Can not start flow!"))
     }

   }

    case HttpRequest(POST, Uri.Path("/flow/stop"), headers, entity, protocol) =>{
      val data = toJson(entity)
      val processId  = data.get("processId").getOrElse("").asInstanceOf[String]
      if(processId.equals("") || !processMap.contains(processId)){
        Future.failed(new Exception("Can not found process Error!"))
      }else{

        val result = API.stopFlow(processMap.get(processId).asInstanceOf[Process])
        Future.successful(HttpResponse(entity = result))
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
