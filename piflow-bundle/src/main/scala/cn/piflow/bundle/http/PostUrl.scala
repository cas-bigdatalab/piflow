//package cn.piflow.bundle.http
//
//import java.io.{BufferedReader, InputStreamReader}
//import java.net.URI
//
//import cn.piflow.conf.bean.PropertyDescriptor
//import cn.piflow.conf.util.{ImageUtil, MapUtil}
//import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
//import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
//import org.apache.hadoop.conf.Configuration
//import org.apache.hadoop.fs.{FSDataInputStream, FileSystem, Path}
//import org.apache.http.client.methods.HttpPost
//import org.apache.http.entity.StringEntity
//import org.apache.http.impl.client.HttpClients
//import org.apache.http.util.EntityUtils
//import org.apache.spark.sql.SparkSession
//
//
//class PostUrl extends ConfigurableStop{
//  override val authorEmail: String = "ygang@cnic.com"
//  override val inportList: List[String] = List(Port.DefaultPort)
//  override val outportList: List[String] = List(Port.DefaultPort)
//  override val description: String = "Send a post request to the specified http"
//
//  var url : String= _
//  var jsonPath : String = _
//
//
//  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
//    val spark = pec.get[SparkSession]()
//
//    //read  json from hdfs
//    val conf = new Configuration()
//    val fs = FileSystem.get(URI.create(jsonPath),conf)
//    val stream: FSDataInputStream = fs.open(new Path(jsonPath))
//    val bufferReader = new BufferedReader(new InputStreamReader(stream))
//    var lineTxt = bufferReader.readLine()
//    val buffer = new StringBuffer()
//    while (lineTxt != null ){
//      buffer.append(lineTxt.mkString)
//      lineTxt=bufferReader.readLine()
//    }
//
//    // post
//    val client = HttpClients.createDefault()
//    val httpClient = new HttpClient()
//    httpClient.getParams().setContentCharset("utf-8")
//
//    val post = new HttpPost(url)
//    post.addHeader("content-Type","application/json")
//    post.setEntity(new StringEntity(buffer.toString))
//    val response = client.execute(post)
//    val entity = response.getEntity
//    val str = EntityUtils.toString(entity,"UTF-8")
//    println("Code is " + str)
//
//  }
//
//
//  override def setProperties(map: Map[String, Any]): Unit = {
//    url = MapUtil.get(map,key="url").asInstanceOf[String]
//    jsonPath = MapUtil.get(map,key="jsonPath").asInstanceOf[String]
//  }
//
//  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
//    var descriptor : List[PropertyDescriptor] = List()
//    val url = new PropertyDescriptor()
//      .name("url")
//      .displayName("Url")
//      .defaultValue("")
//      .description("http request address")
//      .required(true)
//      .example("http://master:8002/flow/start")
//
//    val jsonPath = new PropertyDescriptor()
//      .name("jsonPath")
//      .displayName("JsonPath")
//      .defaultValue("")
//      .description("json parameter path for post request")
//      .required(true)
//        .example("hdfs://master:9000/work/flow.json")
//
//    descriptor = url :: descriptor
//    descriptor = jsonPath :: descriptor
//    descriptor
//  }
//
//  override def getIcon(): Array[Byte] = {
//    ImageUtil.getImage("icon/http/PostUrl.png")
//  }
//
//  override def getGroup(): List[String] = {
//    List(StopGroup.HttpGroup.toString)
//  }
//
//  override def initialize(ctx: ProcessContext): Unit = {
//
//  }
//
//}
