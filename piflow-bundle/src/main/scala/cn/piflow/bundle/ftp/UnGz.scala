package cn.piflow.bundle.ftp

import java.util
import java.util.zip.GZIPInputStream

import cn.piflow.bundle.util.UnGzUtil
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}


class UnGz extends ConfigurableStop{
  val authorEmail: String = "xiaoxiao@cnic.cn"
  val description: String = "Load file from ftp url."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)

  var gzType:String =_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    import spark.sqlContext.implicits._

    val inDf = in.read()
    inDf.show()
    inDf.schema.printTreeString()

    // df => Array[Row]
    val rows: Array[Row] = inDf.collect()
    var df:DataFrame = null

    var count = 0
    for (i <- 0 until rows.size) {

      //row(i)    [/ftpUrlDownLoadDIR555/gbbct151.seq.gz]

      // 文件 路径
      val sourceFile = rows(i)(0).toString
      // println(sourceFile+"----------------------------------")

      if(sourceFile.endsWith("seq.gz")){


        if (count == 0){
          println(count+"-------------------------------")

          // 加载文件为 byteArray
          val byteArray: Array[Byte] = UnGzUtil.unGzStream(sourceFile)

          df = Seq(byteArray).toDF()
          count = count+1
        } else {
          println(count+"-------------------------------")
          val byteArray: Array[Byte] = UnGzUtil.unGzStream(sourceFile)

          df = df.union(Seq(byteArray).toDF())
        }
      }
    }

    df.schema.printTreeString()
    println(df.count())
    out.write(df)

  }


  def setProperties(map: Map[String, Any]): Unit = {

    gzType=MapUtil.get(map,key="gzType").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val gzType = new PropertyDescriptor().name("gzType").displayName("gzType").defaultValue("").required(true)
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