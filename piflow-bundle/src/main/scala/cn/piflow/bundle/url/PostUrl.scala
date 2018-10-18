package cn.piflow.bundle.url

import java.io.{BufferedReader, FileReader, InputStreamReader}
import java.net.URI

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.commons.httpclient.HttpClient
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FileSystem, Path}
import org.apache.hadoop.hdfs.client.HdfsUtils
import org.apache.http.client.methods.HttpPost
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.spark.sql.SparkSession

import scala.io.Source
import scala.util.parsing.json.JSONObject


class PostUrl extends ConfigurableStop{
  override val authorEmail: String = "ygang@cmic.com"
  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
  override val description: String = "peforms an HTTP Post with "

  var url : String= _
  var jsonPath : String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

//    val path = "hdfs://10.0.86.89:9000/yg/test.json"
//    val path = "hdfs://10.0.86.89:9000/xjzhu/example.json"


    //read  json from hdfs
    val conf = new Configuration()
    val fs = FileSystem.get(URI.create(jsonPath),conf)
    val stream: FSDataInputStream = fs.open(new Path(jsonPath))
    val bufferReader = new BufferedReader(new InputStreamReader(stream))
    var lineTxt = bufferReader.readLine()
    val buffer = new StringBuffer()
    while (lineTxt != null ){

      println(lineTxt)
      buffer.append(lineTxt.mkString)

      lineTxt=bufferReader.readLine()
    }
    println(buffer)



    //    val file = Source.fromFile("hdfs://10.0.86.89:9000/xjzhu/cscd.xml","utf-8")
    //    val buffer = new StringBuffer()
    //    for (line <-file.getLines()){
    //      buffer.append(line)
    //      println(line)
    //    }




    // post
    val client = HttpClients.createDefault()
    val httpClient = new HttpClient()
    httpClient.getParams().setContentCharset("utf-8")

    val post = new HttpPost(url)
    post.addHeader("content-Type","application/json")
    post.setEntity(new StringEntity(buffer.toString()))
    val response = client.execute(post)
    val allHeader = post.getAllHeaders
    val entity = response.getEntity
    println(response+"******")
    println(allHeader+"*******")
    println(entity+"************")





  }


  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,key="url").asInstanceOf[String]
    jsonPath = MapUtil.get(map,key="jsonPath").asInstanceOf[String]
    println(url)
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url = new PropertyDescriptor().name("url").displayName("URL").defaultValue("").required(true)
    val jsonPath = new PropertyDescriptor().name("jsonPath").displayName("JSONPATH").defaultValue("").required(true)
    descriptor = url :: descriptor
    descriptor = jsonPath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.UrlGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
