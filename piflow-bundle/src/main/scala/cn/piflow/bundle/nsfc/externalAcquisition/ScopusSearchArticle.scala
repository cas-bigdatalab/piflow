package cn.piflow.bundle.nsfc.externalAcquisition

import java.io.{ByteArrayInputStream, IOException}
import java.net.URLEncoder
import java.util.regex.{Matcher, Pattern}

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataOutputStream, FileSystem, Path}
import org.apache.hadoop.io.IOUtils
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.SparkSession


class ScopusSearchArticle extends ConfigurableStop {

  override val description: String = "Scopus search article"
  val authorEmail: String = "ygang@cnic.cn"

  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.scopus_articlePort.toString,PortEnum.scopus_article_api_response.toString)


  var author = new StringBuilder
  var intervalTime:String = _
  var apiKey :String= _
  var httpurl :String= _


  var hdfsUrl :String= _
  var hdfsDir :String= _
  var scopusFileName :String= _
  var scopus_api_responseFileName :String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDf = in.read()


    val waitTime = intervalTime.toInt
    var inputStream:ByteArrayInputStream = null

    val scopusFilePath = hdfsUrl+hdfsDir+"/"+scopusFileName
    val scopusOut: FSDataOutputStream = writeHdfs(hdfsUrl,scopusFilePath)

    val scopus_api_responseFilePath = hdfsUrl+hdfsDir+"/"+scopus_api_responseFileName
    val scopus_api_responseOut: FSDataOutputStream = writeHdfs(hdfsUrl,scopus_api_responseFilePath)


    var title :String = null
    var titleUrl:String = null
    var titleJsonString:String = null

    var reg:String = null
    var prismUrl:String = null
    var authorString:String = null
    var authorJsonString:String=null

    var scopus_id:String = null
    var eid:String =null


    try {
      inDf.collect().foreach(x=>{

        title = URLEncoder.encode(x.get(0).asInstanceOf[String],"UTF-8")
        titleUrl = httpurl+s"(${title})&apiKey=${apiKey}&httpAccept=application%2Fjson"
        titleJsonString = getHttp(titleUrl)

        // Filter valid request scoups files
        if(titleJsonString.contains("SCOPUS_ID")) {

          titleJsonString = titleJsonString.replace("\"dc:identifier\":\"SCOPUS_ID:","\"scopus_id\":\"")

          reg = "scopus_id\":\"(.*?)\","
          scopus_id = regula(reg,titleJsonString)
          println(scopus_id)
          //  Request author information
          if (titleJsonString.contains("prism:url")){
            reg = "prism:url\":\"(.*?)\","
            prismUrl= regula(reg,titleJsonString)+s"?field=author&apikey=${apiKey}&httpAccept=application%2Fjson"
            authorJsonString = getHttp(prismUrl)

            reg = "preferred-name\": \\{\n.*?\"ce:given-name\": \"(.*?)\",\n.*?,\n.*?ce:surname\": \"(.*?)\","
            authorString = regulaAuthor(reg,authorJsonString).stripSuffix("#")

            titleJsonString=titleJsonString.replace("\"prism:url\":","\"authorString\":\""+authorString+"\",\"prism:url\":")
          }


          // Request summary information
          if (titleJsonString.contains("eid")){
            reg = "eid\":\"(.*?)\","
            eid = regula(reg,titleJsonString)

          }


          println(scopus_id)
          inputStream = new ByteArrayInputStream((scopus_id+"##&##"+titleJsonString+"##&##"+authorJsonString.replace("\n"," ")+ "\n").getBytes("utf-8"))
          IOUtils.copyBytes(inputStream, scopus_api_responseOut, 4096, false)


          inputStream = new ByteArrayInputStream((titleJsonString.toString + "\n").getBytes("utf-8"))
          IOUtils.copyBytes(inputStream, scopusOut, 4096, false)
        }

        //suspend   (ms)
        Thread.sleep(waitTime*1000)
      })

    }catch {
      case e:IOException => e.printStackTrace()
    }finally {
      if (inputStream!=null) IOUtils.closeStream(inputStream)
      if (scopusOut!=null) IOUtils.closeStream(scopusOut)
      if (scopus_api_responseOut!=null) IOUtils.closeStream(scopus_api_responseOut)
    }



    val frame = spark.read.json(scopusFilePath).select("search-results.entry").createOrReplaceTempView("temp")

    val scopusDF = spark.sql(
      """
        |select explode(entry) as entry from temp
      """.stripMargin).select("entry.scopus_id","entry.dc:title","entry.prism:publicationName",
      "entry.prism:issn","entry.prism:volume","entry.prism:pageRange","entry.prism:doi",
      "entry.subtypeDescription","entry.citedby-count", "entry.affiliation.affilname","entry.authorString")
      .toDF("scopus_id","title","publication_name","issn","volume","page_range","doi",
        "description","citedby_count","affiliation","author")


    //    scopusDF.printSchema()
    //    scopusDF.show()



    import spark.implicits._
    val rdd: RDD[String] = spark.sparkContext.textFile("hdfs://192.168.3.138:8020/nsfc/externalData/scoups/scopus.txt")
    val responseDF = rdd.map(x=>{
      val scopus_id =  x.split("##&##")(0)
      val scopus_search_response=x.split("##&##")(1)
      val authors_affiliations_response=x.split("##&##")(2)
      val description_response= ""
      (scopus_id,scopus_search_response,authors_affiliations_response,description_response)
    }).toDF("scopus_id","scopus_search_response","authors_affiliations_response","description_response")

    //    responseDF.printSchema()
    //    responseDF.show()

    out.write(PortEnum.scopus_articlePort,scopusDF)
    out.write(PortEnum.scopus_article_api_response,responseDF)




  }


  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    intervalTime=MapUtil.get(map,key="intervalTime").asInstanceOf[String]
    apiKey 				=MapUtil.get(map,key="apiKey").asInstanceOf[String]
    httpurl       =MapUtil.get(map,key="httpurl").asInstanceOf[String]
    hdfsUrl       =MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsDir       =MapUtil.get(map,key="hdfsDir").asInstanceOf[String]
    scopusFileName  =MapUtil.get(map,key="scopusFileName").asInstanceOf[String]
    scopus_api_responseFileName =MapUtil.get(map,key="scopus_api_responseFileName").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val intervalTime     = new PropertyDescriptor().name("intervalTime").displayName("intervalTime").description("interval time Number of seconds(The minimum number is 0.001)").defaultValue("").required(true)
    val apiKey       = new PropertyDescriptor().name("apiKey").displayName("apiKey").description("scopusAPIKey").defaultValue("").required(true)
    val httpurl      = new PropertyDescriptor().name("httpurl").displayName("httpurl").description("httpurl").defaultValue("").required(true)
    val hdfsUrl      = new PropertyDescriptor().name("hdfsUrl").displayName("hdfsUrl").description("hdfsUrl").defaultValue("").required(true)
    val hdfsDir      = new PropertyDescriptor().name("hdfsDir").displayName("hdfsDir").description("hdfsDir").defaultValue("").required(true)
    val scopusFileName = new PropertyDescriptor().name("scopusFileName").displayName("scopusFileName").description("scopusFileName").defaultValue("scopus.json").required(true)
    val scopus_api_responseFileName = new PropertyDescriptor().name("scopus_api_responseFileName").displayName("scopus_api_responseFileName").description("scopus_api_responseFileName").defaultValue("scopus.txt").required(true)


    descriptor = intervalTime :: descriptor
    descriptor = apiKey :: descriptor
    descriptor = httpurl :: descriptor
    descriptor = hdfsUrl :: descriptor
    descriptor = hdfsDir :: descriptor
    descriptor = scopusFileName :: descriptor
    descriptor = scopus_api_responseFileName :: descriptor

    descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/nsfc/scopus.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.NSFC.toString)
  }


  def writeHdfs(hdfsUrl:String,filePath:String):FSDataOutputStream  ={

    val config = new Configuration()
    config.set("dfs.support.append","true")
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)

    val outPath:Path = new Path(filePath)
    var outputStream:FSDataOutputStream=fs.create(outPath)
    return outputStream

  }



  def getHttp(url:String): String ={

    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val jsonString = EntityUtils.toString(entity,"UTF-8")

    return jsonString
  }


  var value:String = null
  def regula(reg:String,orgString:String) :String ={
    val pattern: Pattern = Pattern.compile(reg)
    val matcher: Matcher = pattern.matcher(orgString.toString)
    if (matcher.find()) value = matcher.group(1)
    else value = "value not exists"

    return value
  }

  def regulaAuthor(reg:String,orgString:String) :StringBuilder ={
    val pattern: Pattern = Pattern.compile(reg)
    val matcher: Matcher = pattern.matcher(orgString.toString)
    while (matcher.find()) author.append(matcher.group(2)+" "+matcher.group(1)+"#")
    return author
  }



}
