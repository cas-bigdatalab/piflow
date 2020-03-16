package cn.piflow.bundle.asr

import java.io.{File, FileNotFoundException}

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.http.entity.ContentType
import org.apache.http.util.EntityUtils
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.json.JSONObject

import scala.collection.mutable.ArrayBuffer

class ChineseSpeechRecognition extends ConfigurableStop {

  val authorEmail: String = "huchuan0901@163.com"
  val description: String = "Speech recognition"
  val inportList: List[String] = List(Port.AnyPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)

  //val url = "http://10.0.86.128:8081/service/classify/asr/"

  var audioPath:String = _
  var url:String =_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val session: SparkSession = pec.get[SparkSession]()

    //read
    var paths = new ArrayBuffer[String]()
    session.read.textFile(audioPath).rdd.collect().foreach(each =>{
      paths+=each
    })

    //
    import org.apache.http.client.config.RequestConfig
    import org.apache.http.client.methods.HttpPost
    import org.apache.http.entity.mime.MultipartEntityBuilder
    import org.apache.http.impl.client.HttpClientBuilder

    val httpClient = HttpClientBuilder.create.build

    val requestConfig = RequestConfig.custom.setConnectTimeout(200000).setSocketTimeout(200000000).build

    var rows: ArrayBuffer[Row] = new ArrayBuffer[Row]

    paths.foreach(path =>{

      val httpPost = new HttpPost(url)
      httpPost.setConfig(requestConfig)
      val multipartEntityBuilder = MultipartEntityBuilder.create

      try {
        val file = new File(path)
        if (file.exists()) {
          //println("start post")
          multipartEntityBuilder.addBinaryBody("audio1", file,ContentType.create("audio/wav"),"audio1")
          val httpEntity = multipartEntityBuilder.build
          httpPost.setEntity(httpEntity)
          val httpResponse = httpClient.execute(httpPost)
          val responseEntity = httpResponse.getEntity
          val statusCode = httpResponse.getStatusLine.getStatusCode
          if (statusCode == 200) {

            val result = new JSONObject(EntityUtils.toString(responseEntity))
            val arr = Array(path,result.getString("error"),result.getString("value"),result.getBoolean("res").toString)
            rows+= Row.fromSeq(arr)

          }
          if (httpResponse != null) httpResponse.close
        }
      }catch{
        case e: FileNotFoundException => println("file not found: "+path)
      }


    })
    httpClient.close
    val rowRDD: RDD[Row] = session.sparkContext.makeRDD(rows)
    val schema: StructType = StructType(Array(
      StructField("audiopath",StringType),
      StructField("error",StringType),
      StructField("value",StringType),
      StructField("res",StringType)
    ))
    val df: DataFrame = session.createDataFrame(rowRDD,schema)

    out.write(df)


  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    audioPath = MapUtil.get(map,"audioPath").asInstanceOf[String]
    url = MapUtil.get(map,"url").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val audioPath = new PropertyDescriptor().name("audioPath").displayName("audioPath").description("The path of audio file").defaultValue("").required(true)
    descriptor = audioPath :: descriptor
    val url = new PropertyDescriptor().name("url").displayName("url").description("The url of the API").defaultValue("http://10.0.86.128:8081/service/classify/asr/").required(false)
    descriptor = url :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/asr/ASR.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Alg_ASRGroup.toString)
  }

}
