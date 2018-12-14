package cn.piflow.bundle.ftp


import java.util

import cn.piflow.bundle.util.UnGzUtil
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}


class UnGz extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "UnZip seq.gz "
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var gzType:String =_
  var transType:String =_
  var localPath:String =_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    import spark.sqlContext.implicits._

    val inDf = in.read()
    inDf.show()
    inDf.schema.printTreeString()

    // df => Array[Row]
    // 多个 文件路径
    val rows: Array[Row] = inDf.collect()
    var df:DataFrame = null

    var count = 0
    for (i <- 0 until rows.size) {
      //row(i)    [/ftpUrlDownLoadDIR555/gbbct151.seq.gz]
      // 文件 路径
      val sourceFile = rows(i)(0).toString

      // 解压 输出 类型
      if (transType.equals("path")) {
        // 解压 .tar.gz  文件
        if (gzType.equals(".tar.gz")) {
           // 第一个 tar.gz  文件
           if (i == 0){
             val strings: util.ArrayList[String] = UnGzUtil.unTarGz(sourceFile,localPath)
             for (k <- 0 until strings.size){
               if (k == 0 ) {
                 // tar.gz 中的第一个文件 路径
                 val filePath = strings.get(k)
                 //  生成 df 的 第一条数据
                 df = Seq(filePath).toDF()
               } else { // 后续文件， 合并为一个  df
                 val filePath = strings.get(i)
                 df = df.union(Seq(filePath).toDF())
               }
             }
           } else {  // i > 0 第2 ～～ n 个 tar.gz文件
             val strings: util.ArrayList[String] = UnGzUtil.unTarGz(sourceFile,localPath)
             for (k <- 0 until strings.size){
               // 与 第一个tar.gz文件 合并 为 一个df
               val filePath = strings.get(i)
               df = df.union(Seq(filePath).toDF())
             }
           }


        } else if(gzType.equals(".gz")){  // 解压 .gz 文件
          // gbbct151.seq.gz
          val fileNameAdd: String = sourceFile.substring(sourceFile.lastIndexOf("/")+1)
          // gbbct151.seq
          val fileName = fileNameAdd.substring(0,fileNameAdd.length-3)
          //  /ftpUrlDownLoadDIR555/gbbct151.seq.gz1234567890
          val  sourceFileAdd = sourceFile+"1234567890"
          //    localPath  +  /ftpUrlDownLoadDIR555/
          val savePath: String =localPath + sourceFileAdd.replaceAll(fileNameAdd+"1234567890","")
          if (i == 0){
            val filePath: String = UnGzUtil.unGz(sourceFile,savePath,fileName)
            println("解压完成----->"+filePath)
            df = Seq(filePath).toDF()
          } else {
            val filePath: String = UnGzUtil.unGz(sourceFile,savePath,fileName)
            println("解压完成----->"+filePath)
            df = df.union(Seq(filePath).toDF())
          }
        }



      } else if (transType.equals("stream")){

        if(sourceFile.endsWith(".gz")){
          if (count == 0){
            println(count+"-------------------------------")
            // 加载文件为 byteArray
            val byteArray: Array[Byte] = UnGzUtil.unGzStream(sourceFile)

            df = Seq(byteArray).toDF()
          } else {
            println(count+"-------------------------------")
            val byteArray: Array[Byte] = UnGzUtil.unGzStream(sourceFile)

            df = df.union(Seq(byteArray).toDF())
          }
        }
      }



    }
//    df.schema.printTreeString()
//    println(df.count())
    out.write(df)
  }


  def setProperties(map: Map[String, Any]): Unit = {
    gzType=MapUtil.get(map,key="gzType").asInstanceOf[String]
    transType=MapUtil.get(map,key="transType").asInstanceOf[String]
    localPath=MapUtil.get(map,key="localPath").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val transType = new PropertyDescriptor().name("transType").displayName("transType").defaultValue("path,stream").required(true)
    descriptor = transType :: descriptor

    val localPath = new PropertyDescriptor().name("localPath").displayName("localPath").defaultValue("/").required(true)
    descriptor = localPath :: descriptor

    val gzType = new PropertyDescriptor().name("gzType").displayName("gzType").defaultValue(".tar.gz,.gz").required(true)
    descriptor = gzType :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("gz.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.FtpGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}