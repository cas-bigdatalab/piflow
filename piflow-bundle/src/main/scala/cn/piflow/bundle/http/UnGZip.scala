package cn.piflow.bundle.http

import java.io.{ByteArrayInputStream, File, FileInputStream, FileOutputStream}
import java.lang.Exception
import java.util.zip.GZIPInputStream

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.commons.compress.archivers.tar.{TarArchiveEntry, TarArchiveInputStream}
import org.apache.spark.sql.{DataFrame, SparkSession}

class UnGZip extends ConfigurableStop {
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Unzip tar.gz, tar, gz file."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  val fileTypes:List[String]=List("tar.gz","tar","gz")
  val outPutDir="/unzip"

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val df = in.read()
    var outDF:DataFrame=null
    import spark.sqlContext.implicits._
    val bis:ByteArrayInputStream=new ByteArrayInputStream(df.head().get(0).asInstanceOf[Array[Byte]])
    val filename=df.head().get(1).asInstanceOf[String]//.replace(".gz","")
    val extention=getExtension(filename)
    var filePath:String=null
    var filePathList:List[String]=null
    if(extention.equals("gz")){
      filePath=unGz(bis,filename)
      outDF=Seq((filePath)).toDF()
      outDF.show(20)
    }
    if(extention.equals("tar")){
      filePathList=unTar(bis,filename)
      outDF=Seq(filePathList).toDF()
      outDF.show(20)
    }
    if(extention.equals("tar.gz")){
      filePathList=unTarGz(bis,filename)
      outDF=Seq(filePathList).toDF()
      outDF.show(20)
    }



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

  def createDir(outPutDir:String,subDir:String):Unit={
    var file:File=new File(outPutDir)
    if(!(subDir==null || subDir.trim=="")){
      file=new File(outPutDir+File.separator+subDir)
    }
    if(!file.exists()){
      file.mkdirs()
    }
  }

  def unGz(bis:ByteArrayInputStream,srcFileName:String):String={
    val gzip:GZIPInputStream=new GZIPInputStream(bis)
    val savePath=new File(outPutDir)
    createDir(outPutDir,null)
    /*if(!savePath.exists()){
      savePath.mkdir()
    }*/
    val fileName:String=savePath+"/"+srcFileName.replace(".gz","")
    val fos:FileOutputStream=new FileOutputStream(fileName)
    var mark = -1
    val buf=new Array[Byte](4*1024)
    while((mark=gzip.read(buf)) != -1 && mark != -1){
      fos.write(buf,0,mark)
    }
    return fileName
  }

  def unTar(bis:ByteArrayInputStream,filename:String):List[String]={
    var entryNum:Int=0
    var entryFileName:String=null
    var entryFile:File=null
    var subEntryFile:File=null
    var subEntryFileName:String=null
    var tarArchiveEntries:Array[TarArchiveEntry]=null
    var fileList:List[String]=List()
    var fos:FileOutputStream=null

    var entry: TarArchiveEntry = null
    val tarIs: TarArchiveInputStream = new TarArchiveInputStream(bis)
    while ((entry = tarIs.getNextTarEntry) != null && entry != null) {
      entryFileName=outPutDir+File.separator+entry.getName()
      entryFile=new File(entryFileName)
      entryNum += 1
      if(entry.isDirectory()){
        if(!entryFile.exists()){
          entryFile.mkdirs()
        }
        tarArchiveEntries=entry.getDirectoryEntries()
        for(i<-0 until tarArchiveEntries.length){
          subEntryFileName=entryFileName+File.separator+tarArchiveEntries(i).getName()
          subEntryFile=new File(subEntryFileName)
          fileList=subEntryFileName::fileList
          fos=new FileOutputStream(subEntryFile)
          var mark = -1
          val buf=new Array[Byte](4*1024)
          while((mark=tarIs.read(buf)) != -1 && mark != -1){
            fos.write(buf,0,mark)
          }
          fos.close()
          fos=null
        }
      }else{
        fileList = entryFileName :: fileList
        fos=new FileOutputStream(entryFile)
        var mark = -1
        val buf=new Array[Byte](4*1024)
        while((mark=tarIs.read(buf)) != -1 && mark != -1){
          fos.write(buf,0,mark)
        }
        fos.close()
        fos=null
      }

    }
    if(entryNum==0){
      println("there is no file!")
    }
    fileList
  }

  def unTarGz(bis:ByteArrayInputStream,filename:String):List[String]={
    var entryNum:Int=0
    var entryFileName:String=null
    var entryFile:File=null
    var subEntryFile:File=null
    var subEntryFileName:String=null
    var tarArchiveEntries:Array[TarArchiveEntry]=null
    var fileList:List[String]=List()
    var fos:FileOutputStream=null

    var entry: TarArchiveEntry = null
    val gzip:GZIPInputStream=new GZIPInputStream(bis)
    val tarIs: TarArchiveInputStream = new TarArchiveInputStream(gzip)
    while ((entry = tarIs.getNextTarEntry) != null && entry != null) {
      entryFileName=outPutDir+File.separator+entry.getName()
      entryFile=new File(entryFileName)
      entryNum += 1
      if(entry.isDirectory()){
        if(!entryFile.exists()){
          entryFile.mkdirs()
        }
        tarArchiveEntries=entry.getDirectoryEntries()
        for(i<-0 until tarArchiveEntries.length){
          subEntryFileName=entryFileName+File.separator+tarArchiveEntries(i).getName()
          subEntryFile=new File(subEntryFileName)
          fileList=subEntryFileName::fileList
          fos=new FileOutputStream(subEntryFile)
          var mark = -1
          val buf=new Array[Byte](4*1024)
          while((mark=tarIs.read(buf)) != -1 && mark != -1){
            fos.write(buf,0,mark)
          }
          fos.close()
          fos=null
        }
      }else{
        fileList = entryFileName :: fileList
        fos=new FileOutputStream(entryFile)
        var mark = -1
        val buf=new Array[Byte](4*1024)
        while((mark=tarIs.read(buf)) != -1 && mark != -1){
          fos.write(buf,0,mark)
        }
        fos.close()
        fos=null
      }

    }
    if(entryNum==0){
      println("there is no file!")
    }
    fileList
  }



  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    return descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("http.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HttpGroup.toString)
  }

}
