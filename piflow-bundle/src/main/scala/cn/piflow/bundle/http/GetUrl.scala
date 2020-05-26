package cn.piflow.bundle.http

import java.util

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.dom4j.{Document, DocumentHelper, Element}

import scala.collection.JavaConverters._
import scala.collection.mutable.{ArrayBuffer, ListBuffer}


class GetUrl extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.com"
  override val description: String = "Send a get request to the specified http"

  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)


  var url :String= _
  var httpAcceptTypes :String = _

  // xml String
  var label:String=_
  var schema: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val ss = pec.get[SparkSession]()
    if (httpAcceptTypes == "json"){
      val client = HttpClients.createDefault()
      val getFlowInfo:HttpGet = new HttpGet(url)
      getFlowInfo.addHeader("Accept",s"application/${httpAcceptTypes}")

      val response:CloseableHttpResponse = client.execute(getFlowInfo)
      val entity = response.getEntity
      val jsonString = EntityUtils.toString(entity,"UTF-8")
      println(jsonString)

      val jsonRDD = ss.sparkContext.makeRDD(jsonString :: Nil)
      val jsonDF = ss.read.json(jsonRDD)
      jsonDF.printSchema()
      out.write(jsonDF)
    }
    if(httpAcceptTypes=="xml"){

      val client = HttpClients.createDefault()
      val getFlowInfo:HttpGet = new HttpGet(url)
      getFlowInfo.addHeader("Accept",s"application/${httpAcceptTypes}")

      val response:CloseableHttpResponse = client.execute(getFlowInfo)
      val entity = response.getEntity
      val jsonString = EntityUtils.toString(entity,"UTF-8")
      println(jsonString)

      val doc: Document = DocumentHelper.parseText(jsonString)
      val rootElt: Element = doc.getRootElement
      var arrbuffer:ArrayBuffer[Element]=ArrayBuffer()
      arrbuffer+=rootElt

      val arrLabel: Array[String] = label.split(",").map(x => x.trim)
      for(x<-(1 until arrLabel.length)){
        var ele: Element =null
        if(x==1){
          ele = rootElt.element(arrLabel(x).toString)
        }else{
          ele = arrbuffer(x-2).element(arrLabel(x).toString)
        }
        arrbuffer+=ele
      }

      val FatherElement: Element = arrbuffer(arrbuffer.size-2)

      val arrSchame: Array[String] = schema.split(",").map(x=>x.trim)

      var list:ListBuffer[String]=ListBuffer()


      val FatherInterator: util.Iterator[_] = FatherElement.elementIterator(arrbuffer.last.getName)
      val scalaIterator: Iterator[Element] = FatherInterator.asInstanceOf[util.Iterator[Element]].asScala

      while (scalaIterator.hasNext){
        val value: Element = scalaIterator.next()
        var text: String =""
        for(each<-arrSchame){
          text += value.element(each).getText+","
        }
        list.+=(text.substring(0,text.length-1))
      }

      val listRows: List[Row] = list.toList.map(line => {
        val seq: Seq[String] = line.split(",").map(x => x.trim).toSeq
        val row = Row.fromSeq(seq)
        row
      })
      val rowRDD: RDD[Row] = ss.sparkContext.makeRDD(listRows)


      val fields: Array[StructField] = arrSchame.map(p => {
        StructField(p, StringType, nullable = true)
      })
      val structType: StructType = StructType(fields)

      val outDf: DataFrame = ss.createDataFrame(rowRDD,structType)

      out.write(outDf)
    }




  }
  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,key="url").asInstanceOf[String]
    httpAcceptTypes= MapUtil.get(map,key="httpAcceptTypes").asInstanceOf[String]
    label = MapUtil.get(map,"label").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url = new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .defaultValue("")
      .description("http request address")
      .required(true)
        .example("https://api.elsevier.com/content/search/scopus?query=TITLE('title')&apiKey=555637gxd\"")
     descriptor = url :: descriptor

    val httpAcceptTypes = new PropertyDescriptor()
      .name("httpAcceptTypes")
      .displayName("HttpAcceptTypes")
      .allowableValues(Set("xml","json"))
      .defaultValue("json")
      .description("The type of data you want to receive)")
      .required(true)
        .example("xml")
    descriptor = httpAcceptTypes :: descriptor

    val label = new PropertyDescriptor()
      .name("label")
      .displayName("Label")
      .description("Parsed label path (types is xml)")
      .defaultValue("")
      .required(false)
        .example("service-error,status")
    descriptor = label :: descriptor

    val schema = new PropertyDescriptor()
      .name("schema")
      .displayName("Schema")
      .description("Parsed tag name (types is xml)")
      .defaultValue("")
      .required(false)
        .example("statusCode,statusText")
    descriptor = schema :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/http/GetUrl.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HttpGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
