package cn.piflow.bundle.internetWorm

import java.io.{BufferedOutputStream, File, FileOutputStream, InputStream}
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.jsoup.Jsoup
import org.jsoup.nodes.{Document, Element}
import org.jsoup.select.Elements

import scala.collection.mutable.ArrayBuffer

class spider extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Crawl data from websites"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)


  var rootUrl:String=_
  var firstUrl:String=_
  var markupField:String=_
  var jumpDependence:String=_
  var fileMap:String=_
  var downPath:String=_


  var map:Map[String,String]=Map()
  var array:ArrayBuffer[Map[String,String]]=ArrayBuffer()
  var countInt:Int=0

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val session: SparkSession = pec.get[SparkSession]()

    var doc: Document =null
    val selectArr: Array[String] = jumpDependence.split("/")
    try{
       doc = Jsoup.connect(firstUrl).timeout(50000).get()
    }catch {
      case e:Exception => throw new RuntimeException("The page specified by firstUrl does not exist."+"\n"+"firstUrl指定的页面不存在")
    }
    var eles: Elements = null
    try{
      eles = doc.select(selectArr(0))
    }catch {
      case e:Exception => throw new RuntimeException("JumpDependence specified label path does not exist."+"\n"+"jumpDependence指定的标签路径不存在")
    }
    var choiceIntArr: Array[Int] =0.until(eles.size()).toArray

    if(selectArr.size>1){
       choiceIntArr=selectArr(1).toInt.until(eles.size()).toArray
    }
    for(x <- choiceIntArr){
      var num=x
      if(selectArr.size==3){
        num = x + countInt * (selectArr(2).toInt)
      }
      val ele = eles.get(num)
      var textStr: String = ele.text()
      if(textStr.length==0){
        textStr = " "
        throw  new RuntimeException("Label field no value"+"\n"+"标记字段无值")
      }
      map+=(markupField->textStr)
      val hrefStr: String = ele.attr("href")
      val strArr: Array[String] = fileMap.split("\\+")
      parseNext(rootUrl+hrefStr,strArr)
      array+=map

      countInt+=1
    }
    countInt=0
    var keySet: Set[String] =Set()
    val rows1: List[Row] = array.toList.map(map => {
      keySet = map.keySet
      val values: Iterable[AnyRef] = map.values
      val seq: Seq[AnyRef] = values.toSeq
      val seqSTR: Seq[String] = values.toSeq.map(x=>x.toString)
      val row: Row = Row.fromSeq(seqSTR)
      row
    })
    val rowRDD: RDD[Row] = session.sparkContext.makeRDD(rows1)
    val fields: Array[StructField] = keySet.toArray.map(d=>StructField(d,StringType,nullable = true))
    val schema: StructType = StructType(fields)
    val df: DataFrame = session.createDataFrame(rowRDD,schema)

    out.write(df)
  }


  def parseNext(url:String,strArr: Array[String]): Unit = {
    var doc: Document = null
    try {
      doc = Jsoup.connect(url).timeout(50000).get()

    } catch {
        case e: IllegalArgumentException => throw new RuntimeException("The two level interface path does not exist."+"\n"+"二层界面路径不存在")
    }
    var textDownFile:File =null
    for(each <- strArr){
      val fileMapArr: Array[String] = each.split("/")
      val els: Elements = doc.select(fileMapArr(1))
      val numEle: Element = els.get(fileMapArr(2).toInt)
      if(fileMapArr(0).indexOf("DOWN")> -1){
        val downDoc: Document = Jsoup.connect(rootUrl+numEle.attr("href").substring(3)).get()
        val downList = downDoc.select(fileMapArr(3))
        val rangeArr: Array[String] = fileMapArr(4).split("-")
        for(r <- (rangeArr(0).toInt until rangeArr(1).toInt) ){
          val eachFileEle: Element = downList.get(r)
          if(downPath.size==0){
            downPath="/InternetWormDown/"
          }
          map+=("downPath"->downPath)
          val nowDate: String = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date())
          map+=("downDate"->nowDate)
          textDownFile = new File(downPath+map.get(markupField).get)
          if(! textDownFile.exists()){
            textDownFile.mkdirs()
          }
          val eachFile: File = new File(downPath+map.get(markupField).get+"/"+eachFileEle.text())
          if(!eachFile.exists()){
            val in: InputStream = new URL(url+eachFileEle.attr("href")).openStream()
            val out: BufferedOutputStream = new BufferedOutputStream(new FileOutputStream(eachFile),10485760)
            val buff: Array[Byte] = new Array[Byte](1048576)

            var count:Int=in.read(buff)
            while(count!= -1){
              out.write(buff,0,count)
              out.flush()
              count=in.read(buff)
            }
            in.close()
            out.close()

        }

        }
      }else{
        if(fileMapArr.size > 2){
          map+=(fileMapArr(0) -> numEle.text())
        }else{
          map+=(fileMapArr(0) -> els.get(0).text())
      }
      }
    }
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    rootUrl = MapUtil.get(map,"rootUrl").asInstanceOf[String]
    markupField = MapUtil.get(map,"markupField").asInstanceOf[String]
    firstUrl = MapUtil.get(map,"firstUrl").asInstanceOf[String]
    jumpDependence = MapUtil.get(map,"jumpDependence").asInstanceOf[String]
    fileMap = MapUtil.get(map,"fileMap").asInstanceOf[String]
    downPath = MapUtil.get(map,"downPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val rootUrl=new PropertyDescriptor().name("rootUrl").displayName("rootUrl").description("The domain name address of Web site that needs to crawl data.").defaultValue("").required(true)
    descriptor = rootUrl :: descriptor
    val markupField=new PropertyDescriptor().name("markupField").displayName("markupField").description("The field name of the collection obtained from the first level interface.").defaultValue("").required(true)
    descriptor = markupField :: descriptor
    val firstUrl=new PropertyDescriptor().name("firstUrl").displayName("firstUrl").description("Address of the first level interface of website").defaultValue("").required(true)
    descriptor = firstUrl :: descriptor
    val jumpDependence=new PropertyDescriptor().name("jumpDependence").displayName("jumpDependence").description("Href access to the second tier interface").defaultValue("").required(true)
    descriptor = jumpDependence :: descriptor
    val fileMap=new PropertyDescriptor().name("fileMap").displayName("fileMap").description("The fields and label paths you want, and the location of the data, " +
      "are separated by /, and different fields are connected by'+'. If you want to specify a link to the download list, " +
      "you can do so.Number of Instances/html>body>table>tbody>tr>td>table>tbody>tr>td>p.normal/4+Data Set Characteristics/html>body>table>tbody>tr>td>table>tbody>tr>td>p.normal/2+DOWN/html>body>table>tbody>tr>td>table>tbody>tr>td>p>span.normal>a/0/html>body>table>tbody>tr>td>a/1-2").defaultValue("").required(true)
    descriptor = fileMap :: descriptor
    val downPath=new PropertyDescriptor().name("downPath").displayName("downPath").description("The path of the dataset you want to save").defaultValue("").required(false)
    descriptor = downPath :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/internetWorm/Spider.png")

  }

  override def getGroup(): List[String] = {
    List(StopGroup.Spider.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {}

}
