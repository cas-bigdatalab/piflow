package cn.piflow.bundle.unstructured

import akka.actor.ActorSystem
import akka.http.scaladsl.Http
import akka.http.scaladsl.model.HttpMethods.GET
import akka.http.scaladsl.model._
import akka.util.Timeout
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil, ProcessUtil, UnstructuredUtils}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.util.PropertyUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

import java.net.URLEncoder
import scala.collection.mutable.ArrayBuffer
import scala.concurrent.duration.DurationInt
import scala.concurrent.{Await, Future}

class ImageParser extends ConfigurableStop {
  val authorEmail: String = "tianyao@cnic.cn"
  val description: String = "parse pdf to structured data."
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var filePath: String = _
  var fileSource: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val serverPort = PropertyUtil.getIntPropertyValue("server.port")
    val unstructuredHost: String = PropertyUtil.getPropertyValue("unstructured.host")
    var unstructuredPort: String = PropertyUtil.getPropertyValue("unstructured.port")
    if (unstructuredHost.isEmpty) {
      println("########## Exception: can not parse, unstructured host is null!!!")
      throw new Exception("########## Exception: can not parse, unstructured host is null!!!")
    } else if ("127.0.0.1".equals(unstructuredHost) || "localhost".equals(unstructuredHost)) {
      println("########## Exception: can not parse, the unstructured host cannot be set to localhost!!!")
      throw new Exception("########## Exception: can not parse, the unstructured host cannot be set to localhost!!!")
    }
    if (unstructuredPort.isEmpty) unstructuredPort = "8000"

    //If the file path contains Spaces or special characters, you may need to use URLEncoder for encoding
    filePath = URLEncoder.encode(filePath, "UTF-8").replace("+", "%20"); // 替换+为%20，因为URL编码中+代表空格

    if ("hdfs".equals(fileSource)) {
      //Download the file to the location where the unstructured server resides
      //1.Create an ActorSystem, which is the basis for all asynchronous operations in Akka
      implicit val system = ActorSystem("httpClient")
      implicit val timeout: Timeout = Timeout(10.minutes) // 设置超时时间

      val baseUrl = s"$unstructuredHost:$serverPort/hdfs/downloadFile"

      //2.Build the complete URL, including the query parameters
      val url = Uri(baseUrl).withQuery(Uri.Query("filePath" -> filePath))
      val responseFuture: Future[HttpResponse] = Http().singleRequest(HttpRequest(GET, url))
      val response: HttpResponse = Await.result(responseFuture, timeout.duration)
      response.status match {
        case StatusCodes.OK =>
        case _ =>
          println(s"Request failed with status ${response.status}")
          throw new Exception("########## Exception: can not parse, file is not available!!!")
      }
      val localTempPath = "/data/temp/files/"
      filePath = localTempPath + UnstructuredUtils.extractFileNameWithExtension(filePath)
      // close ActorSystem
      system.terminate()
    }

    //Create a mutable ArrayBuffer to store the parameters of the curl command
    val curlCommandParams = new ArrayBuffer[String]()
    curlCommandParams += "curl"
    curlCommandParams += "-X"
    curlCommandParams += "POST"
    curlCommandParams += s"$unstructuredHost:$unstructuredPort/general/v0/general"
    curlCommandParams += "-H"
    curlCommandParams += "accept: application/json"
    curlCommandParams += "-H"
    curlCommandParams += "Content-Type: multipart/form-data"
    curlCommandParams += "-F"
    curlCommandParams += s"files=@$filePath"

    val (output, error): (String, String) = ProcessUtil.executeCommand(curlCommandParams.toSeq)
    if (error.nonEmpty) {
      println(s"########## Exception: $error")
      throw new Exception(s"########## Exception: $error")
    }
//    if ("hdfs".equals(fileSource)) {
//      //Delete file
//
//    }

    //Convert output to dataframe
    //Register a JSON string as a temporary view
    spark.read.json(output).createOrReplaceTempView("jsonTable")
    //Define a schema. Because of the nested structure in JSON data, we need to define a complex schema
    val schema = new org.apache.spark.sql.types.StructType(
      Array(
        new org.apache.spark.sql.types.StructField("type", org.apache.spark.sql.types.StringType, true),
        new org.apache.spark.sql.types.StructField("element_id", org.apache.spark.sql.types.StringType, true),
        new org.apache.spark.sql.types.StructField("text", org.apache.spark.sql.types.StringType, true),
        new org.apache.spark.sql.types.StructField("metadata", new org.apache.spark.sql.types.StructType(
          Array(
            new org.apache.spark.sql.types.StructField("languages", org.apache.spark.sql.types.ArrayType(org.apache.spark.sql.types.StringType), true),
            new org.apache.spark.sql.types.StructField("page_number", org.apache.spark.sql.types.IntegerType, true),
            new org.apache.spark.sql.types.StructField("filename", org.apache.spark.sql.types.StringType, true),
            new org.apache.spark.sql.types.StructField("filetype", org.apache.spark.sql.types.StringType, true)
          )
        ), true)
      )
    )

    //The temporary view is read using the defined schema and converted to a DataFrame
    val df = spark.read.schema(schema).json(output)
    out.write(df)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    filePath = MapUtil.get(map, "filePath").asInstanceOf[String]
    fileSource = MapUtil.get(map, "fileSource").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    val filePath = new PropertyDescriptor()
      .name("filePath")
      .displayName("FilePath")
      .description("The path of the file(.png/.jpg/.jpeg/.tiff/.bmp/.heic)")
      .defaultValue("")
      .required(true)
      .example("/test/test.png")
    descriptor = descriptor :+ filePath

    val fileSource = new PropertyDescriptor()
      .name("fileSource")
      .displayName("FileSource")
      .description("The source of the file ")
      .defaultValue("true")
      .allowableValues(Set("hdfs", "nfs"))
      .required(true)
      .example("hdfs")
    descriptor = descriptor :+ fileSource

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/unstructured/ImageParser.png", this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List("unstructured")
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
