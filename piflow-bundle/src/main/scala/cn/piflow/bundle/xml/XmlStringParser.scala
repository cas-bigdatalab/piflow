package cn.piflow.bundle.xml

import java.util

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.dom4j.{Document, DocumentHelper, Element}

import scala.collection.JavaConverters._
import scala.collection.mutable.{ArrayBuffer, ListBuffer}

class XmlStringParser extends ConfigurableStop {
  override val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  override val description: String = "Parse xml string"

  var XmlString:String=_
  var label:String=_
  var schema: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val doc: Document = DocumentHelper.parseText(XmlString)
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

    val arrSchame: Array[String] = schema.split(",").map(x => x.trim)

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
      val seq: Seq[String] = line.split(",").toSeq
      val row = Row.fromSeq(seq)
      row
    })
    val rowRDD: RDD[Row] = spark.sparkContext.makeRDD(listRows)


    val fields: Array[StructField] = arrSchame.map(p => {
      StructField(p, StringType, nullable = true)
    })
    val structType: StructType = StructType(fields)

    val Fdf: DataFrame = spark.createDataFrame(rowRDD,structType)

    //Fdf.show(20)
    out.write(Fdf)


  }

  def StrToFile(str: String): Unit = {


  }

  override def setProperties(map: Map[String, Any]): Unit = {
    XmlString = MapUtil.get(map,"XmlString").asInstanceOf[String]
    label = MapUtil.get(map,"label").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] =  {
    var descriptor : List[PropertyDescriptor] = List()
    val XmlString = new PropertyDescriptor()
      .name("XmlString")
      .displayName("XmlString")
      .description("the xml String")
      .defaultValue("")
      .required(true)
      .example("<sites>\n    <site>\n        <name>菜鸟教程</name>\n        <url>www.runoob.com</url>\n    </site>\n    <site>\n        <name>Google</name>\n        <url>www.google.com</url>\n    </site>\n    <site>\n        <name>淘宝</name>\n        <url>www.taobao.com</url>\n    </site>\n</sites>")

    descriptor = XmlString :: descriptor
    val label = new PropertyDescriptor()
      .name("label")
      .displayName("label")
      .description("Parsed label path")
      .defaultValue("")
      .required(true)
        .example("sites,site")

    descriptor = label :: descriptor
    val schema = new PropertyDescriptor()
      .name("schema")
      .displayName("schema")
      .description("Parsed tag name")
      .defaultValue("")
      .required(true)
        .example("name,url")
    descriptor = schema :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/xml/XmlStringParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.XmlGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
