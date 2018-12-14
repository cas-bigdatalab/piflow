package cn.piflow.bundle.http

import java.io._
import java.net.{HttpURLConnection, URL}

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class LoadZipFromUrl extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "DownLoad zip file by http."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  var url_str:String =_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val url=new URL(url_str)
    val uc:HttpURLConnection=url.openConnection().asInstanceOf[HttpURLConnection]
    uc.setDoInput(true)
    uc.connect()
    val inputStream:InputStream=uc.getInputStream()
    val size=uc.getContentLength
    /*val savePath=new File("/xx/dblp/")
    if(!savePath.exists()){
      savePath.mkdir()
    }
    println("*********savePath run****************")*/
    val urlname = url_str.split("/")
    val len=urlname.length
    val filename=urlname(len-1)
    /*val file_path=savePath+"/"+filename
    val file=new File(file_path)
    if(file!=null || !file.exists()){
      file.createNewFile()
    }
    println("*********file create************")

    val outputStream=new FileOutputStream(file)*/
    println(size)
    var byteArrayOutputStream:ByteArrayOutputStream=new ByteArrayOutputStream()
    val buffer=new Array[Byte](1024*1024)
    var byteRead= -1
    val spark = pec.get[SparkSession]()
    import spark.sqlContext.implicits._
    var count=0
    while(((byteRead=inputStream.read(buffer)) != -1) && (byteRead != -1)){
      count=count+1
      println(count+":"+byteRead)
      byteArrayOutputStream.write(buffer,0,byteRead)
    }
    val df_create_start_time=System.currentTimeMillis()
    val byteArray=byteArrayOutputStream.toByteArray
    val df=Seq((byteArray,filename)).toDF()
    val df_create_end_time=System.currentTimeMillis()
    println("df_create_time="+(df_create_end_time - df_create_start_time))
    val df_write_start_time=System.currentTimeMillis()
    out.write(df)
    val df_write_end_time=System.currentTimeMillis()
    println("df_write_time="+(df_write_end_time - df_write_start_time))
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    url_str=MapUtil.get(map,key="url_str").asInstanceOf[String]
    //file_Path=MapUtil.get(map,key="file_Path").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url_str = new PropertyDescriptor().name("url_str").displayName("URL").defaultValue("").required(true)
    //val file_Path = new PropertyDescriptor().name("file_Path").displayName("File_Path").defaultValue("").required(true)
    descriptor = url_str :: descriptor
    //descriptor = file_Path :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("http.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HttpGroup.toString)
  }


}
