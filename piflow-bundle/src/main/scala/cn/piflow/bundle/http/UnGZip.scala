package cn.piflow.bundle.http

import java.io.{ByteArrayInputStream, File, FileOutputStream}
import java.util.zip.GZIPInputStream

import cn.piflow.conf.{ConfigurableStop, HiveGroup, HttpGroup, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class UnGZip extends ConfigurableStop {
  val inportCount: Int = 0
  val outportCount: Int = 1
  val fileTypes:List[String]=List("tar.gz","tar","gz")

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val df = in.read()
    val bis:ByteArrayInputStream=new ByteArrayInputStream(df.head().get(0).asInstanceOf[Array[Byte]])
    val gzip:GZIPInputStream=new GZIPInputStream(bis)
    val savePath=new File("/unzip")
    if(!savePath.exists()){
      savePath.mkdir()
    }
    val filePath:String=savePath+"/"+df.head().get(1).asInstanceOf[String].replace(".gz","")
    val fos:FileOutputStream=new FileOutputStream(filePath)
    var mark = -1
    val buf=new Array[Byte](4*1024)
    while((mark=gzip.read(buf)) != -1 && mark != -1){
      fos.write(buf,0,mark)

    }
    import spark.sqlContext.implicits._
    val outDF=Seq((filePath)).toDF()
    out.write(outDF)
  }

  def getExtension(filename:String):String={
      for(i<-0 until fileTypes.length){
        if(filename.endsWith("."+fileTypes(i))){
          return fileTypes(i)
        }
      }
      return null
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = null
    return descriptor
  }

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): StopGroup = {
    HttpGroup
  }

}
