package cn.piflow.bundle.xml

import java.net.URI

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf._
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}

import scala.collection.mutable.ArrayBuffer
import scala.util.control.Breaks._

/**
  * Created by admin on 2018/8/27.
  */
class XmlParserFolder extends ConfigurableStop{
  val authorEmail: String = "lijie"
  val description: String = "Parse xml folder"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var rowTag:String = _
  var xmlpath:String = _
  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val pathArr = getFileName(xmlpath)
    val xmlDF = getResDf(pathArr,spark)
    //xmlDF.show(30)
    out.write(xmlDF)
  }
  override def setProperties(map: Map[String, Any]): Unit = {
    xmlpath = MapUtil.get(map,"xmlpath").asInstanceOf[String]
    rowTag = MapUtil.get(map,"rowTag").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val xmlpath = new PropertyDescriptor()
      .name("xmlpath")
      .displayName("xmlpath")
      .defaultValue("")
      .required(true)
      .example("/work/test/xml/")

    val rowTag = new PropertyDescriptor()
      .name("rowTag")
      .displayName("rowTag")
      .description("the tag you want to parse in xml file")
      .defaultValue("")
      .required(true)
        .example("name,url")

    descriptor = xmlpath :: descriptor
    descriptor = rowTag :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/xml/FolderXmlParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.XmlGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit ={}

  //获取.xml所有文件路径
  def getFileName(path:String):ArrayBuffer[String]={
    var arr = ArrayBuffer[String]()
      val conf = new Configuration()
      val fs = FileSystem.get(URI.create(path), conf)
      val statuses = fs.listStatus(new Path(path))
      for (i <- statuses) {
        if(!i.isDirectory){
        if (i.getPath().getName.endsWith(".xml")) {
          arr+=i.getPath.toString
        }
        }else{
          val arr1 = getFileName(i.getPath.toString)
          arr=arr++(arr1)
        }
      }
    arr
  }
  //获取每个xml得dataframe
  def getDf(path:String,sparkSession: SparkSession):DataFrame={
    val df = sparkSession.read.format("com.databricks.spark.xml")
      .option("rowTag", rowTag)
      .option("treatEmptyValuesAsNulls", true)
      .load(path)
    df
  }
  //获取文件夹最终得dataframe
  def getResDf(pathArr:ArrayBuffer[String],spark:SparkSession):DataFrame={
    var index =0
    breakable{
      for(i <- 0 until pathArr.length){
        if(getDf(pathArr(i),spark).count()!=0){
          index=i
          break
        }
      }
    }
    var df = spark.read.format("com.databricks.spark.xml")
      .option("rowTag", rowTag)
      .option("treatEmptyValuesAsNulls", true)
      .load(pathArr(index))
    for(d <- index+1 until(pathArr.length)){
      if(getDf(pathArr(d),spark).count()!=0){
        val df1 = spark.read.format("com.databricks.spark.xml")
          .option("rowTag", rowTag)
          .option("treatEmptyValuesAsNulls", true)
          .load(pathArr(d))
        df = df.union(df1)
      }
    }
    df
  }
}

