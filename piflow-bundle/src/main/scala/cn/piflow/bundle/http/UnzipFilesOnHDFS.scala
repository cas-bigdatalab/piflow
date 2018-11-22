package cn.piflow.bundle.http

import java.util.zip.GZIPInputStream

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

class UnzipFilesOnHDFS extends ConfigurableStop {
  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "Unzip files on HDFS"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var filePath:String=_
  var fileType:String=_
  var unzipPath:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val session: SparkSession = pec.get[SparkSession]()

    val configuration: Configuration = new Configuration()
    val fs = FileSystem.get(configuration)
    val fdis: FSDataInputStream = fs.open(new Path(filePath))


    val filePathArr: Array[String] = filePath.split("/")
    var fileName: String = filePathArr.last
    if(fileName.length == 0){
      fileName = filePathArr(filePathArr.size-2)
    }

    if(fileType.equals("gz")){

      val gzip: GZIPInputStream = new GZIPInputStream(fdis)
      var n = -1
      val buf=new Array[Byte](10*1024*1024)
      val savePath = new Path(unzipPath +fileName.replace(".gz",""))
      val fdos = fs.create(savePath)
      while((n=gzip.read(buf)) != -1 && n != -1){
        fdos.write(buf,0,n)
        fdos.flush()
      }


    }/*else if(fileType.equals("tar")){

      var entryNum:Int=0
      var entryFileName:String=null
      var entryFile:File=null
      var subEntryFile:File=null
      var subEntryFileName:String=null
      var tarArchiveEntries:Array[TarArchiveEntry]=null
      var fileList:List[String]=List()
      var fos:FileOutputStream=null

      var entry: TarArchiveEntry = null
      val tarIs: TarArchiveInputStream = new TarArchiveInputStream(fdis)
      while ((entry = tarIs.getNextTarEntry) != null && entry != null) {
        entryFileName= localPath +File.separator+entry.getName()
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

    }else if(fileType.equals("tar.gz")){

      var entryNum:Int=0
      var entryFileName:String=null
      var entryFile:File=null
      var subEntryFile:File=null
      var subEntryFileName:String=null
      var tarArchiveEntries:Array[TarArchiveEntry]=null
      var fileList:List[String]=List()
      var fos:FileOutputStream=null

      var entry: TarArchiveEntry = null
      val gzip:GZIPInputStream=new GZIPInputStream(fdis)
      val tarIs: TarArchiveInputStream = new TarArchiveInputStream(gzip)
      while ((entry = tarIs.getNextTarEntry) != null && entry != null) {
        entryFileName=localPath +File.separator+entry.getName()
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
    }*/else{
      throw new RuntimeException("File type fill in error, or do not support this type.")
    }

    var seq:Seq[String]=Seq(unzipPath)
    val row: Row = Row.fromSeq(seq)
    val list:List[Row]=List(row)
    val rdd: RDD[Row] = session.sparkContext.makeRDD(list)
    val fields: Array[StructField] =Array(StructField("unzipPath",StringType,nullable = true))
    val schema: StructType = StructType(fields)
    val df: DataFrame = session.createDataFrame(rdd,schema)

    out.write(df)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    filePath=MapUtil.get(map,key="filePath").asInstanceOf[String]
    fileType=MapUtil.get(map,key="fileType").asInstanceOf[String]
    unzipPath=MapUtil.get(map,key="unzipPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val filePath = new PropertyDescriptor().name("filePath").displayName("filePath").description("file path,such as hdfs://10.0.86.89:9000/a/a.gz").defaultValue("").required(true)
    val fileType = new PropertyDescriptor().name("fileType").displayName("fileType").description("file type,such as gz").defaultValue("").required(true)
    val unzipPath = new PropertyDescriptor().name("unzipPath").displayName("unzipPath").description("unzip path, such as hdfs://10.0.86.89:9000/b/").defaultValue("").required(true)
    descriptor = filePath :: descriptor
    descriptor = fileType :: descriptor
    descriptor = unzipPath :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("http.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.HttpGroup.toString)
  }

}
