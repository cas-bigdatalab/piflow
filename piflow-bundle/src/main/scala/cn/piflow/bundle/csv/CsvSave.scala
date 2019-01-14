package cn.piflow.bundle.csv

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import org.apache.spark.sql.SaveMode

class CsvSave extends ConfigurableStop{
  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Save data into csv file."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)

  var csvSavePath: String = _
  var header: Boolean = _
  var delimiter: String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    csvSavePath = MapUtil.get(map,"csvSavePath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String].toBoolean
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    //csvSavePath
    val csvSavePath = new PropertyDescriptor().name("csvSavePath").displayName("csvSavePath").description("The save path of csv file").defaultValue("").required(true)
    descriptor = csvSavePath :: descriptor

    //header
    val header = new PropertyDescriptor().name("header").displayName("header").description("Whether the csv file have header or not").defaultValue("").required(true)
    descriptor = header :: descriptor

    //delimiter
    val delimiter = new PropertyDescriptor().name("delimiter").displayName("delimiter").description("The delimiter of csv file").defaultValue(",").required(true)
    descriptor = delimiter :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("csv.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CsvGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()
    //df.show()
    df.write
      .format("csv")
      .mode(SaveMode.Overwrite)
      .option("header", header)
      .save(csvSavePath)
  }
}

