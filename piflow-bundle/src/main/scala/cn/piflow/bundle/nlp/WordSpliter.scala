package cn.piflow.bundle.nlp

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import com.huaban.analysis.jieba.JiebaSegmenter.SegMode
import com.huaban.analysis.jieba._
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

import scala.collection.JavaConverters._
import scala.collection.mutable.ArrayBuffer

class WordSpliter extends ConfigurableStop {

  val authorEmail: String = "huchuan0901@163.com"
  val description: String = "Word segmentation"
  val inportList: List[String] = List(Port.AnyPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)

  var path:String = _


  val jiebaSegmenter = new JiebaSegmenter()
  var tokenARR:ArrayBuffer[String]=ArrayBuffer()

  def segmenter(str:String): Unit ={

    var strVar = str
    //delete symbol
    strVar = strVar.replaceAll( "[\\p{P}+~$`^=|<>～｀＄＾＋＝｜＜＞￥×+\\s]" , "");

    val tokens = jiebaSegmenter.process(strVar,SegMode.SEARCH).asScala

    for (token: SegToken <- tokens){

        tokenARR += token.word

    }
  }

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val session: SparkSession = pec.get[SparkSession]()

    //read
    val strDF = session.read.text(path)

    //segmenter
    segmenter(strDF.head().getString(0))

    //write df
    val rows: List[Row] = tokenARR.map(each => {
      var arr:Array[String]=Array(each)
      val row: Row = Row.fromSeq(arr)
      row
    }).toList
    val rowRDD: RDD[Row] = session.sparkContext.makeRDD(rows)
    val schema: StructType = StructType(Array(
      StructField("words",StringType)
    ))
    val df: DataFrame = session.createDataFrame(rowRDD,schema)

    out.write(df)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    path = MapUtil.get(map,"path").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val path = new PropertyDescriptor().name("path").displayName("path").description("The path of text file").defaultValue("").required(true)
    descriptor = path :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/nlp/NLP.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Alg_NLPGroup.toString)
  }

}
