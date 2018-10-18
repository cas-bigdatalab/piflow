package cn.piflow.bundle.url

import java.io.PrintWriter

import cn.piflow._
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{FileUtil, MapUtil, OptionUtil}
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.sql.{Row, SparkSession}

import scala.io.Source


class GetUrl extends ConfigurableStop{
  override val authorEmail: String = "ygang@cmic.com"


  override val description: String = "Get data from http/url to dataframe"

  var url :String= _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()


    // get from url
    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val jsonString = EntityUtils.toString(entity,"UTF-8")


    // save local
    //    val fileCount = Source.fromURL(url,"utf-8").mkString
    //    val pe = new PrintWriter("/opt/tet/test1.json")
    //    pe.write(fileCount)
    //    pe.flush()


    // json to df
    val jsonRDD = spark.sparkContext.makeRDD(jsonString :: Nil)
    val jsonDF = spark.read.json(jsonRDD)

    //println(jsonDF.schema.printTreeString())

    //jsonDF.select("app.id").printSchema()

    jsonDF.show(10)
    out.write(jsonDF)

    //test post
//    val post = new HttpPost(url)
//    post.addHeader("content-Type","application/json")
//    post.setEntity(new StringEntity(jsonString))
//    val response1 = client.execute(post)
//    val allHeader = post.getAllHeaders
//    val entity1 = response1.getEntity
//
//    println(response+"-----")
//    println(allHeader+"-----")
//    println(entity1+"-----")

  }


  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,key="url").asInstanceOf[String]
    //    schema=MapUtil.get(map,key = "schema").asInstanceOf[String]
    println(url)
    //    println(schema)
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url = new PropertyDescriptor().name("url").displayName("URL").defaultValue("").required(true)
    descriptor = url :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.UrlGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
}
