package cn.cnic.bigdatalab.server

import akka.actor.ActorSystem
import akka.stream.ActorMaterializer
import akka.http.scaladsl.Http
import akka.http.scaladsl.marshallers.sprayjson.SprayJsonSupport
import akka.http.scaladsl.server.Directives
import cn.cnic.bigdatalab.utils.PropertyUtil
import spray.json.DefaultJsonProtocol
import akka.http.scaladsl.model.HttpMethods._
import akka.http.scaladsl.model._
import com.typesafe.config.ConfigFactory

import scala.concurrent.Future
import scala.util.parsing.json.JSON

/**
  * Created by Flora on 2016/8/8.
  */
object HTTPService2 extends DefaultJsonProtocol with Directives with SprayJsonSupport{
  implicit val system = ActorSystem("HTTPService2", ConfigFactory.load())
  implicit val materializer = ActorMaterializer()

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

    case HttpRequest(POST, Uri.Path("/task/v2/create"), headers, entity, protocol) =>{
      val data = toJson(entity)
      if(!data.get("agentId").isEmpty && !data.get("taskId").isEmpty){
        val result = API.runRealTimeTask(data.get("agentId").get.asInstanceOf[String], data.get("taskId").get.asInstanceOf[String])
        Future.successful(HttpResponse(entity = result))
      }else if(!data.get("taskId").isEmpty){
        val result = API.runOfflineTask(data.get("taskId").get.asInstanceOf[String])
        Future.successful(HttpResponse(entity = result))
      }else{
        Future.successful(HttpResponse(entity = "Param Error!"))
      }
    }

    case HttpRequest(DELETE, Uri.Path("/task/v2/delete"), headers, entity, protocol) =>{
      val data = toJson(entity)
      if(data.get("name").isEmpty){
        Future.successful(HttpResponse(entity = "Param Error!"))
      }else{
        val result = API.deleteTask(data.get("name").get.asInstanceOf[String])
        Future.successful(HttpResponse(entity = result))
      }
    }

    case HttpRequest(PUT, Uri.Path("/task/v2/stop"), headers, entity, protocol) =>{
      val data = toJson(entity)
      if(data.get("name").isEmpty){
        Future.successful(HttpResponse(entity = "Param Error!"))
      }else{
        val result = API.stopTask(data.get("name").get.asInstanceOf[String])
        Future.successful(HttpResponse(entity = result))
      }
    }

    case HttpRequest(PUT, Uri.Path("/task/v2/start"), headers, entity, protocol) =>{
      val data = toJson(entity)
      if(data.get("name").isEmpty){
        Future.successful(HttpResponse(entity = "Param Error!"))
      }else{
        val result = API.startTask(data.get("name").get.asInstanceOf[String])
        Future.successful(HttpResponse(entity = result))
      }
    }

    case _: HttpRequest =>
      Future.successful(HttpResponse(404, entity = "Unknown resource!"))
  }

  def run = {
    val ip = PropertyUtil.getPropertyValue("server_ip")
    val port = PropertyUtil.getIntPropertyValue("server_port")
    Http().bindAndHandleAsync(route, ip, port)
    println("Server:" + ip + ":" + port + " Started!!!")
  }

}

object Main {
  def main(argv: Array[String]):Unit = {
    HTTPService2.run
  }
}
