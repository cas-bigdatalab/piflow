package cn.piflow.bundle.http

import java.io.{BufferedReader, InputStreamReader}
import java.net.URI
import java.util

import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FileSystem, Path}
import org.apache.http.client.methods._
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.dom4j.{Document, DocumentHelper, Element}

import scala.collection.JavaConverters._
import scala.collection.mutable.{ArrayBuffer, ListBuffer}

class InvokeUrl extends ConfigurableStop{
  override val authorEmail: String = "ygang@cmic.com"
  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
  override val description: String = "invoke http "

//  var urlPut :String= _
//  var urlPost :String= _
//  var urlDelete :String= _
//  var urlGet :String= _

  var url :String= _
  var jsonPath :String =_
  var method :String = _
  var colume : String = _

  // xml get
  var label:String=_
  var schema: String = _
  var xmlString :String=_
  var types :String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val client = HttpClients.createDefault()

    if (method == "getHttp") {
      val getFlowInfo: HttpGet = new HttpGet(url)

      val response: CloseableHttpResponse = client.execute(getFlowInfo)
      val entity = response.getEntity
      val jsonString = EntityUtils.toString(entity, "UTF-8")

      println("=====================================================================invoke get")

      // json to df
      if (types == "json") {
        // json to df
        val jsonRDD = spark.sparkContext.makeRDD(jsonString :: Nil)
        val jsonDF = spark.read.json(jsonRDD)

        jsonDF.schema.printTreeString()
        jsonDF.show(10)
        jsonDF.select("app.id").show()
        out.write(jsonDF)
      }
      if (types == "xml") {

        val doc: Document = DocumentHelper.parseText(xmlString)
        val rootElt: Element = doc.getRootElement
        var arrbuffer: ArrayBuffer[Element] = ArrayBuffer()
        arrbuffer += rootElt

        val arrLabel: Array[String] = label.split(",")
        for (x <- (1 until arrLabel.length)) {
          var ele: Element = null
          if (x == 1) {
            ele = rootElt.element(arrLabel(x).toString)
          } else {
            ele = arrbuffer(x - 2).element(arrLabel(x).toString)
          }
          arrbuffer += ele
        }

        val FatherElement: Element = arrbuffer(arrbuffer.size - 2)

        val arrSchame: Array[String] = schema.split(",")

        var list: ListBuffer[String] = ListBuffer()


        val FatherInterator: util.Iterator[_] = FatherElement.elementIterator(arrbuffer.last.getName)
        val scalaIterator: Iterator[Element] = FatherInterator.asInstanceOf[util.Iterator[Element]].asScala

        while (scalaIterator.hasNext) {
          val value: Element = scalaIterator.next()
          var text: String = ""
          for (each <- arrSchame) {
            text += value.element(each).getText + ","
          }
          list.+=(text.substring(0, text.length - 1))
        }


        val listRows: List[Row] = list.toList.map(line => {
          val seq: Seq[String] = line.split(",").toSeq
          val row = Row.fromSeq(seq)
          row
        })
        val rowRDD: RDD[Row] = spark.sparkContext.makeRDD(listRows)


        val fields: Array[StructField] = arrSchame.map(p => {
          StructField(p, StringType, nullable = true)
        })
        val structType: StructType = StructType(fields)

        val outDf: DataFrame = spark.createDataFrame(rowRDD, structType)

        outDf.show(20)
        outDf.schema.printTreeString()
        out.write(outDf)

        println("====================================================================")

      }


      if (method == "putHttp" || method == "postHttp") {
        //read  json from hdfs
        val conf = new Configuration()
        val fs = FileSystem.get(URI.create(jsonPath), conf)
        val stream: FSDataInputStream = fs.open(new Path(jsonPath))
        val bufferReader = new BufferedReader(new InputStreamReader(stream))
        var lineTxt = bufferReader.readLine()
        val buffer = new StringBuffer()
        while (lineTxt != null) {
          buffer.append(lineTxt.mkString)
          lineTxt = bufferReader.readLine()
        }
        println(buffer)

        if (method == "putHttp") {
          val put = new HttpPut(url)
          put.setHeader("content-Type", "application/json")
          //put.setHeader("Accept","application/json")
          put.setEntity(new StringEntity(buffer.toString, "utf-8"))

          val response = client.execute(put)
          val entity = response.getEntity
          var result = ""
          if (entity != null) {
            result = EntityUtils.toString(entity, "utf-8")
          }
          println(response)
          println(result)
          put.releaseConnection()
        } else {
          val post = new HttpPost(url)
          post.setHeader("content-Type", "application/json")
          post.setEntity(new StringEntity(buffer.toString))

          val response = client.execute(post)
          val entity = response.getEntity
          val str = EntityUtils.toString(entity, "UTF-8")
          println(response)
          println("Code is " + str)
        }
      }

      if (method == "deleteHttp") {
        println(url)
        val inDf = in.read()

        inDf.createOrReplaceTempView("table")
        val sqlDF = inDf.sqlContext.sql(s"select $colume from table")
        sqlDF.show()

        val array = sqlDF.collect()


        for (i <- 0 until array.length) {
          var url1 = ""
          val newArray = array(i)

          var builder = new StringBuilder
          for (i <- 0 until newArray.length) {
            val columns = colume.split(",")
            if (i == newArray.length - 1) {
              builder.append(columns(i) + "=" + newArray(i))
            } else {
              builder.append(columns(i) + "=" + newArray(i) + "&")
            }
          }
          //  println(builder)

          url1 = url + "?" + builder
          println(url1 + "##########################################################")

          val delete = new HttpDelete(url1)
          delete.setHeader("content-Type", "application/json")

          val response = client.execute(delete)
          val entity = response.getEntity
          val str = EntityUtils.toString(entity, "UTF-8")
          println("Code is " + str)
          println(response)

        }


      }
    }
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,key="url").asInstanceOf[String]
//    urlPut = MapUtil.get(map,key="urlPut").asInstanceOf[String]
//    urlPost = MapUtil.get(map,key="urlPost").asInstanceOf[String]
//    urlDelete = MapUtil.get(map,key="urlDelete").asInstanceOf[String]
//    urlGet = MapUtil.get(map,key="urlGet").asInstanceOf[String]
    jsonPath = MapUtil.get(map,key="jsonPath").asInstanceOf[String]
    method = MapUtil.get(map,key = "method").asInstanceOf[String]

    //delete
    colume = MapUtil.get(map,key = "colume").asInstanceOf[String]

//  get xml
    xmlString = MapUtil.get(map,"XmlString").asInstanceOf[String]
    label = MapUtil.get(map,"label").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
//    val urlPut = new PropertyDescriptor().name("urlPut").displayName("urlPutPost").defaultValue("").required(true)
//    val urlPost = new PropertyDescriptor().name("urlPost").displayName("urlPutPost").defaultValue("").required(true)
//    val urlDelete = new PropertyDescriptor().name("urlDelete").displayName("urlPutPost").defaultValue("").required(true)
//    val urlGet = new PropertyDescriptor().name("urlGet").displayName("urlGet").defaultValue("").required(true)
    val url = new PropertyDescriptor().name("url").displayName("url").defaultValue("").required(true)
    val jsonPath = new PropertyDescriptor().name("jsonPath").displayName("JSONPATH").defaultValue("").required(true)
    val method = new PropertyDescriptor().name("method").displayName("the way with http").defaultValue("").required(true)
    val colume = new PropertyDescriptor().name("colume").displayName("colume").defaultValue("").required(true)

    val types = new PropertyDescriptor().name("types").displayName("types").defaultValue("the url content is json or xml)").required(true)
    descriptor = types :: descriptor
    val xmlString = new PropertyDescriptor().name("XmlString").displayName("XmlString").description("the xml String").defaultValue("").required(true)
    descriptor = xmlString :: descriptor
    val label = new PropertyDescriptor().name("label").displayName("label").description("label path for hope,the delimiter is ,").defaultValue("").required(true)
    descriptor = label :: descriptor
    val schema = new PropertyDescriptor().name("schema").displayName("schema").description("name of field in label,the delimiter is ,").defaultValue("").required(true)
    descriptor = schema :: descriptor

//    descriptor = urlPut :: descriptor
//    descriptor = urlPost :: descriptor
//    descriptor = urlDelete :: descriptor
//    descriptor = urlGet :: descriptor
    descriptor = jsonPath :: descriptor
    descriptor = method :: descriptor
    descriptor = colume :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("http.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.HttpGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
