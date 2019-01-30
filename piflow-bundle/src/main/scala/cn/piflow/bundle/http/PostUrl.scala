package cn.piflow.bundle.http

import java.io.{BufferedReader, InputStreamReader}
import java.net.URI

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.commons.httpclient.HttpClient
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FileSystem, Path}
import org.apache.http.client.methods.HttpPost
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.sql.SparkSession


class PostUrl extends ConfigurableStop{
  override val authorEmail: String = "ygang@cmic.com"
  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
  override val description: String = "peforms an HTTP Post with "

  var url : String= _
  var jsonPath : String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    //read  json from hdfs
    val conf = new Configuration()
    val fs = FileSystem.get(URI.create(jsonPath),conf)
    val stream: FSDataInputStream = fs.open(new Path(jsonPath))
    val bufferReader = new BufferedReader(new InputStreamReader(stream))
    var lineTxt = bufferReader.readLine()
    val buffer = new StringBuffer()
    while (lineTxt != null ){
      buffer.append(lineTxt.mkString)
      lineTxt=bufferReader.readLine()
    }


    // post
    val client = HttpClients.createDefault()
    val httpClient = new HttpClient()
    httpClient.getParams().setContentCharset("utf-8")

    val post = new HttpPost(url)
    post.addHeader("content-Type","application/json")
    post.setEntity(new StringEntity(buffer.toString))
    val response = client.execute(post)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)

  }


  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,key="url").asInstanceOf[String]
    jsonPath = MapUtil.get(map,key="jsonPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url = new PropertyDescriptor().name("url").displayName("url").defaultValue("").required(true)
    val jsonPath = new PropertyDescriptor().name("jsonPath").displayName("jsonPath").defaultValue("").required(true)
    descriptor = url :: descriptor
    descriptor = jsonPath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("http.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HttpGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
