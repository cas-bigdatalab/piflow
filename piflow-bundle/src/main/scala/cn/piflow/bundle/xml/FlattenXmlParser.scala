package cn.piflow.bundle.xml

import java.net.URI
import java.util

import cn.piflow.bundle.util.JsonUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Column, DataFrame, Row, SparkSession}
import org.dom4j.io.SAXReader
import org.dom4j.{Document, DocumentHelper, Element}

import scala.collection.JavaConverters._
import scala.collection.mutable.{ArrayBuffer, ListBuffer}


class FlattenXmlParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val description: String = "Parse the XML file and expand the label you need."


  var xmlpath:String = _
  var tagPath:String = _
  var openTag: String = _
  var returnField: String = _


  def javaIterToScalaIter(utilIter: util.Iterator[_]):Iterator[Element]={
    utilIter.asInstanceOf[util.Iterator[Element]].asScala
  }

  var ss: SparkSession =_
  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {



    ss=pec.get[SparkSession]()
    val conf = new Configuration()
    val fs: FileSystem = FileSystem.get(URI.create(xmlpath), conf)
    val hdfsInputStream: FSDataInputStream = fs.open(new Path(xmlpath))
    val saxReader: SAXReader = new SAXReader()
    val document: Document = saxReader.read(hdfsInputStream)
    val rootElt: Element = document.getRootElement

    var finalDF:DataFrame=null

    var arrbuffer:ArrayBuffer[Element]=ArrayBuffer()
    arrbuffer+=rootElt

    val arrLabel: Array[String] = tagPath.split(",")
    for(x<-(1 until arrLabel.length)){
      var ele: Element =arrbuffer(x-1).element(arrLabel(x))
      arrbuffer+=ele
    }

    val FatherElement: Element = arrbuffer(arrbuffer.size-1)
    val FatherInterator: util.Iterator[_] = FatherElement.elementIterator()
    val scalalInterator: Iterator[Element] = javaIterToScalaIter(FatherInterator)

      var relationKey:String=""
      var relationValue:String=""

    var valueArr:ArrayBuffer[ArrayBuffer[String]]=ArrayBuffer()
    var value:ArrayBuffer[String]=ArrayBuffer()
    var keyArr:ArrayBuffer[String]=ArrayBuffer()

    while (scalalInterator.hasNext){
      val ele: Element = scalalInterator.next()
      if(relationKey.size==0&&relationValue.size==0){
        relationKey=ele.getName
        relationValue=ele.getStringValue
      }
      keyArr+=ele.getName
      value+=ele.getStringValue
    }
    valueArr+=value

    val valRows: List[Row] = valueArr.toList.map(x => {
      val seq = x.toSeq
      val row: Row = Row.fromSeq(seq)
      row
    })
    val fie: Array[StructField] = keyArr.toList.map(d=>StructField(d.toString,StringType,nullable = true)).toArray
    val schame: StructType = StructType(fie)
    finalDF = ss.createDataFrame(ss.sparkContext.makeRDD(valRows),schame)



    if(returnField.size>0){
      val returnARR: Array[String] = returnField.split(",")
      val seq: Seq[Column] = returnARR.map(x=>finalDF(x)).toSeq
      val df: DataFrame = finalDF.select(seq : _*)
      finalDF=df

    }


   var smallDF: DataFrame = null
     if(openTag.size>0){
      val eleExplode: Element = FatherElement.element(openTag)

      val eleExplodeIterator: util.Iterator[_] = eleExplode.elementIterator()
      val explodeScalaIterator: Iterator[Element] = javaIterToScalaIter(eleExplodeIterator)

      var explodeValueArr:ArrayBuffer[ArrayBuffer[String]]=ArrayBuffer()
      var sonKeyArr:ArrayBuffer[String]=ArrayBuffer()
      while (explodeScalaIterator.hasNext){
        val ele: Element = explodeScalaIterator.next()
        val sonEle: util.Iterator[_] = ele.elementIterator()
        val sonScalaInterator = javaIterToScalaIter(sonEle)
        var sonValueArr:ArrayBuffer[String]=ArrayBuffer()
        sonValueArr+=relationValue
        sonKeyArr.clear()
        sonKeyArr +=(relationKey+"_")
        while (sonScalaInterator.hasNext){
          val each: Element = sonScalaInterator.next()
          sonValueArr+=each.getStringValue
          sonKeyArr+=(openTag+"_"+each.getName)
        }
        explodeValueArr+=sonValueArr
      }
      val valueRows: List[Row] = explodeValueArr.toList.map(x => {
        val seq = x.toSeq
        val row: Row = Row.fromSeq(seq)
        row
      })
      val field: Array[StructField] = sonKeyArr.toList.map(d=>StructField(d,StringType,nullable = true)).toArray
      val sonSchame: StructType = StructType(field)
      smallDF = ss.createDataFrame(ss.sparkContext.makeRDD(valueRows),sonSchame)

       val df: DataFrame = smallDF.join(finalDF,finalDF(relationKey)===smallDF(relationKey+"_"),"left")
       finalDF=  df.drop(relationKey+"_")
    }


    println("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    finalDF.show(20)
    println("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    out.write(finalDF)
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    xmlpath = MapUtil.get(map,"xmlpath").asInstanceOf[String]
    tagPath = MapUtil.get(map,"tagPath").asInstanceOf[String]
    openTag = MapUtil.get(map,"openTag").asInstanceOf[String]
    returnField = MapUtil.get(map,"returnField").asInstanceOf[String]
  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] =  {
    var descriptor : List[PropertyDescriptor] = List()
    val xmlpath = new PropertyDescriptor().name("xmlpath").displayName("xmlpath").description("the xml String").defaultValue("").required(true)
    descriptor = xmlpath :: descriptor
    val tagPath = new PropertyDescriptor().name("tagPath").displayName("tagPath").description("The tag path you want to parse,the delimiter is ,").defaultValue("").required(true)
    descriptor = tagPath :: descriptor
    val openTag = new PropertyDescriptor().name("openTag").displayName("openTag").description("The tag you want to expand").defaultValue("").required(false)
    descriptor = openTag :: descriptor
    val returnField = new PropertyDescriptor().name("returnField").displayName("returnField").description("The name of the field you want to return,the delimiter is ,").defaultValue("").required(false)
    descriptor = returnField :: descriptor
    descriptor
  }
  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("xml.png")
  }
  override def getGroup(): List[String] = {
    List(StopGroup.XmlGroup.toString)
  }
  override def initialize(ctx: ProcessContext): Unit = {

  }


}
