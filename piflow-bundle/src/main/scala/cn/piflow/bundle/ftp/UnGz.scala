package cn.piflow.bundle.ftp

import cn.piflow.bundle.util.UnGzUtil
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{Row, SparkSession}


class UnGz extends ConfigurableStop{
  val authorEmail: String = "xiaoxiao@cnic.cn"
  val description: String = "Load file from ftp url."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)

  var localPath:String =_

  var list = List("")

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    import spark.sqlContext.implicits._

    val inDf = in.read()
    inDf.show()
    inDf.schema.printTreeString()

    val rows: Array[Row] = inDf.collect()


      for (i <- 0 until rows.size) {
        val sourceFile = rows(i)(0).toString

        if(sourceFile.endsWith("seq.gz")){
          println(sourceFile+"----------------------------------")
          val strings: Array[String] = sourceFile.split("/")
          val fileName = strings(strings.length-1).split(".gz")(0)
          val savePath = localPath+sourceFile.split(".seq.gz")(0)

          println(savePath)

          val filePath = UnGzUtil.unGz(sourceFile,savePath,fileName)

          println(filePath)
          list = filePath::list
        }
      }

    val df = sc.parallelize(list).toDF("filePath")
    df.schema.printTreeString()
    df.show()
    out.write(df)

  }


  def setProperties(map: Map[String, Any]): Unit = {

    localPath=MapUtil.get(map,key="localPath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val savePath = new PropertyDescriptor().name("savePath").displayName("savePath").defaultValue("").required(true)
    descriptor = savePath :: descriptor
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